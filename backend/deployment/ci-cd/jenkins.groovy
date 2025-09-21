// Jenkins Pipeline for HeatGuard Predictive Safety System
// Declarative pipeline with comprehensive stages for CI/CD

pipeline {
    agent any

    // Global environment variables
    environment {
        // Container registry
        REGISTRY = 'your-registry.com'
        IMAGE_NAME = 'heatguard/api'
        REGISTRY_CREDENTIALS = 'registry-credentials-id'

        // Kubernetes
        KUBECONFIG_DEV = credentials('kubeconfig-dev')
        KUBECONFIG_STAGING = credentials('kubeconfig-staging')
        KUBECONFIG_PROD = credentials('kubeconfig-prod')

        // Application settings
        PYTHON_VERSION = '3.9'
        NODE_VERSION = '18'

        // Monitoring and notifications
        SLACK_WEBHOOK = credentials('slack-webhook-url')
        SONARQUBE_TOKEN = credentials('sonarqube-token')

        // Security scanning
        SNYK_TOKEN = credentials('snyk-token')
        TRIVY_CACHE_DIR = '/tmp/trivy-cache'

        // Performance testing
        K6_CLOUD_TOKEN = credentials('k6-cloud-token')

        // Build metadata
        BUILD_VERSION = "${env.BUILD_NUMBER}-${env.GIT_COMMIT.take(8)}"
        BUILD_TIMESTAMP = new Date().format('yyyy-MM-dd-HH:mm:ss')
    }

    // Pipeline options
    options {
        buildDiscarder(logRotator(
            numToKeepStr: '50',
            daysToKeepStr: '30',
            artifactNumToKeepStr: '20'
        ))
        timeout(time: 60, unit: 'MINUTES')
        retry(1)
        skipStagesAfterUnstable()
        parallelsAlwaysFailFast()
        timestamps()
    }

    // Build triggers
    triggers {
        // Poll SCM for changes every 5 minutes (only for main branch)
        pollSCM(env.BRANCH_NAME == 'main' ? 'H/5 * * * *' : '')

        // Nightly security scans
        cron(env.BRANCH_NAME == 'main' ? '@daily' : '')

        // Webhook trigger for GitHub/GitLab
        githubPush()
    }

    // Build parameters for manual triggers
    parameters {
        choice(
            name: 'DEPLOY_ENVIRONMENT',
            choices: ['none', 'development', 'staging', 'production'],
            description: 'Select environment for deployment'
        )
        booleanParam(
            name: 'RUN_PERFORMANCE_TESTS',
            defaultValue: false,
            description: 'Run performance tests'
        )
        booleanParam(
            name: 'SKIP_TESTS',
            defaultValue: false,
            description: 'Skip test execution (emergency deployments only)'
        )
        string(
            name: 'CUSTOM_IMAGE_TAG',
            defaultValue: '',
            description: 'Custom image tag (leave empty for auto-generated)'
        )
    }

    stages {
        stage('Initialize') {
            steps {
                script {
                    // Set dynamic environment variables
                    env.IMAGE_TAG = params.CUSTOM_IMAGE_TAG ?: "${BUILD_VERSION}"
                    env.FULL_IMAGE_NAME = "${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"

                    // Print build information
                    echo """
                    ====================================
                    HeatGuard CI/CD Pipeline Starting
                    ====================================
                    Branch: ${env.BRANCH_NAME}
                    Commit: ${env.GIT_COMMIT}
                    Build: ${env.BUILD_NUMBER}
                    Image Tag: ${env.IMAGE_TAG}
                    Deploy Target: ${params.DEPLOY_ENVIRONMENT}
                    ====================================
                    """
                }

                // Clean workspace
                cleanWs()

                // Checkout code
                checkout scm

                // Send Slack notification
                slackSend(
                    channel: '#heatguard-ci',
                    color: '#36a64f',
                    message: ":rocket: Starting HeatGuard pipeline for ${env.BRANCH_NAME} - Build #${env.BUILD_NUMBER}"
                )
            }
        }

        stage('Code Quality & Security') {
            parallel {
                stage('Code Quality') {
                    agent {
                        docker {
                            image "python:${PYTHON_VERSION}"
                            args '-u root'
                        }
                    }
                    steps {
                        dir('backend') {
                            sh '''
                                pip install --upgrade pip
                                pip install -r requirements.txt
                                pip install black flake8 mypy bandit safety isort

                                echo "=== Running Black formatter check ==="
                                black --check --diff .

                                echo "=== Running isort import sorting check ==="
                                isort --check-only --diff .

                                echo "=== Running Flake8 linting ==="
                                flake8 app/ --count --select=E9,F63,F7,F82 --show-source --statistics
                                flake8 app/ --count --max-complexity=10 --max-line-length=127 --statistics

                                echo "=== Running MyPy type checking ==="
                                mypy app/ --ignore-missing-imports || true

                                echo "=== Running Bandit security analysis ==="
                                bandit -r app/ -f json -o bandit-report.json
                                bandit -r app/ --severity-level medium

                                echo "=== Checking for known vulnerabilities ==="
                                safety check --json --output safety-report.json || true
                            '''
                        }

                        // Archive security reports
                        archiveArtifacts(
                            artifacts: 'backend/*-report.json',
                            allowEmptyArchive: true,
                            fingerprint: true
                        )
                    }
                    post {
                        always {
                            // Publish security scan results
                            publishHTML([
                                allowMissing: false,
                                alwaysLinkToLastBuild: true,
                                keepAll: true,
                                reportDir: 'backend',
                                reportFiles: 'bandit-report.json',
                                reportName: 'Security Report'
                            ])
                        }
                    }
                }

                stage('SonarQube Analysis') {
                    when {
                        anyOf {
                            branch 'main'
                            branch 'develop'
                            changeRequest()
                        }
                    }
                    steps {
                        script {
                            def scannerHome = tool 'SonarQubeScanner'
                            withSonarQubeEnv('SonarQube') {
                                dir('backend') {
                                    sh """
                                        ${scannerHome}/bin/sonar-scanner \\
                                            -Dsonar.projectKey=heatguard-api \\
                                            -Dsonar.projectName='HeatGuard API' \\
                                            -Dsonar.projectVersion=${BUILD_VERSION} \\
                                            -Dsonar.sources=app/ \\
                                            -Dsonar.tests=tests/ \\
                                            -Dsonar.python.coverage.reportPaths=coverage.xml \\
                                            -Dsonar.python.bandit.reportPaths=bandit-report.json
                                    """
                                }
                            }
                        }

                        // Quality Gate
                        timeout(time: 10, unit: 'MINUTES') {
                            waitForQualityGate abortPipeline: true
                        }
                    }
                }

                stage('Dependency Check') {
                    steps {
                        script {
                            docker.image('owasp/dependency-check:latest').inside('-u root') {
                                dir('backend') {
                                    sh '''
                                        /usr/share/dependency-check/bin/dependency-check.sh \\
                                            --project "HeatGuard API" \\
                                            --scan requirements.txt \\
                                            --format JSON \\
                                            --format HTML \\
                                            --out dependency-check-report
                                    '''
                                }
                            }
                        }

                        archiveArtifacts(
                            artifacts: 'backend/dependency-check-report/*',
                            allowEmptyArchive: true
                        )
                    }
                }
            }
        }

        stage('Tests') {
            when {
                not { params.SKIP_TESTS }
            }
            parallel {
                stage('Unit Tests') {
                    agent {
                        docker {
                            image "python:${PYTHON_VERSION}"
                            args '-u root --network host'
                        }
                    }
                    steps {
                        // Start Redis container for tests
                        script {
                            docker.image('redis:7-alpine').withRun('-p 6379:6379') { redis ->
                                dir('backend') {
                                    sh '''
                                        pip install --upgrade pip
                                        pip install -r requirements.txt
                                        pip install pytest pytest-asyncio pytest-mock pytest-cov

                                        # Wait for Redis
                                        sleep 10

                                        # Run tests with coverage
                                        REDIS_URL=redis://localhost:6379/0 pytest tests/unit/ \\
                                            -v \\
                                            --cov=app \\
                                            --cov-report=xml \\
                                            --cov-report=html \\
                                            --cov-report=term \\
                                            --junitxml=unit-test-results.xml
                                    '''
                                }
                            }
                        }
                    }
                    post {
                        always {
                            // Publish test results
                            junit 'backend/unit-test-results.xml'

                            // Publish coverage report
                            publishCoverage adapters: [
                                coberturaAdapter('backend/coverage.xml')
                            ], sourceFileResolver: sourceFiles('STORE_LAST_BUILD')

                            // Archive coverage HTML report
                            publishHTML([
                                allowMissing: false,
                                alwaysLinkToLastBuild: true,
                                keepAll: true,
                                reportDir: 'backend/htmlcov',
                                reportFiles: 'index.html',
                                reportName: 'Coverage Report'
                            ])
                        }
                    }
                }

                stage('Integration Tests') {
                    agent {
                        docker {
                            image "python:${PYTHON_VERSION}"
                            args '-u root --network host'
                        }
                    }
                    steps {
                        script {
                            docker.image('redis:7-alpine').withRun('-p 6379:6379') { redis ->
                                dir('backend') {
                                    sh '''
                                        pip install --upgrade pip
                                        pip install -r requirements.txt
                                        pip install pytest pytest-asyncio httpx

                                        # Start API server
                                        python demo_api_server.py &
                                        API_PID=$!

                                        # Wait for server to start
                                        sleep 15

                                        # Run integration tests
                                        REDIS_URL=redis://localhost:6379/0 pytest tests/integration/ \\
                                            -v \\
                                            --junitxml=integration-test-results.xml

                                        # Clean up
                                        kill $API_PID || true
                                    '''
                                }
                            }
                        }
                    }
                    post {
                        always {
                            junit 'backend/integration-test-results.xml'
                        }
                    }
                }

                stage('API Tests') {
                    steps {
                        script {
                            docker.image('postman/newman').inside() {
                                dir('backend') {
                                    sh '''
                                        # Start demo API server
                                        python demo_api_server.py &
                                        API_PID=$!
                                        sleep 15

                                        # Run Newman tests
                                        newman run docs/examples/postman_collection.json \\
                                            --environment docs/examples/postman_environment.json \\
                                            --reporters cli,junit \\
                                            --reporter-junit-export newman-results.xml

                                        kill $API_PID || true
                                    '''
                                }
                            }
                        }
                    }
                    post {
                        always {
                            junit 'backend/newman-results.xml'
                        }
                    }
                }
            }
        }

        stage('Performance Tests') {
            when {
                anyOf {
                    params.RUN_PERFORMANCE_TESTS
                    branch 'main'
                }
            }
            steps {
                script {
                    docker.image('grafana/k6:latest').inside() {
                        dir('backend/tests') {
                            sh '''
                                # Start API server
                                python ../demo_api_server.py &
                                API_PID=$!
                                sleep 15

                                # Run K6 performance tests
                                k6 run \\
                                    --out json=load-test-results.json \\
                                    --summary-trend-stats="avg,min,med,max,p(95),p(99)" \\
                                    load-test.js

                                kill $API_PID || true
                            '''
                        }
                    }
                }

                archiveArtifacts(
                    artifacts: 'backend/tests/load-test-results.json',
                    allowEmptyArchive: true
                )
            }
        }

        stage('Build Container') {
            steps {
                script {
                    dir('backend') {
                        // Build container image
                        def image = docker.build(
                            "${FULL_IMAGE_NAME}",
                            """-f deployment/docker/Dockerfile
                               --build-arg VERSION=${BUILD_VERSION}
                               --build-arg BUILD_DATE=${BUILD_TIMESTAMP}
                               ."""
                        )

                        // Tag additional versions
                        if (env.BRANCH_NAME == 'main') {
                            image.tag('latest')
                        }

                        if (env.BRANCH_NAME == 'develop') {
                            image.tag('develop')
                        }

                        // Push to registry
                        docker.withRegistry("https://${REGISTRY}", REGISTRY_CREDENTIALS) {
                            image.push()
                            if (env.BRANCH_NAME == 'main') {
                                image.push('latest')
                            }
                            if (env.BRANCH_NAME == 'develop') {
                                image.push('develop')
                            }
                        }
                    }
                }
            }
        }

        stage('Container Security Scan') {
            parallel {
                stage('Trivy Scan') {
                    steps {
                        script {
                            docker.image('aquasecurity/trivy:latest').inside("-v ${TRIVY_CACHE_DIR}:/cache") {
                                sh """
                                    trivy image \\
                                        --cache-dir /cache \\
                                        --format template \\
                                        --template "@contrib/sarif.tpl" \\
                                        -o trivy-report.sarif \\
                                        ${FULL_IMAGE_NAME}

                                    trivy image \\
                                        --cache-dir /cache \\
                                        --format table \\
                                        ${FULL_IMAGE_NAME}
                                """
                            }
                        }

                        archiveArtifacts(
                            artifacts: 'trivy-report.sarif',
                            allowEmptyArchive: true
                        )
                    }
                }

                stage('Snyk Scan') {
                    when {
                        environment name: 'SNYK_TOKEN', value: ''
                        not { true } // Skip if no Snyk token
                    }
                    steps {
                        script {
                            docker.image('snyk/snyk:docker').inside() {
                                sh """
                                    snyk test --docker ${FULL_IMAGE_NAME} \\
                                        --json-file-output=snyk-report.json || true
                                """
                            }
                        }

                        archiveArtifacts(
                            artifacts: 'snyk-report.json',
                            allowEmptyArchive: true
                        )
                    }
                }
            }
        }

        stage('Deploy to Development') {
            when {
                anyOf {
                    branch 'develop'
                    params.DEPLOY_ENVIRONMENT == 'development'
                }
            }
            environment {
                KUBECONFIG = "${KUBECONFIG_DEV}"
                NAMESPACE = 'heatguard-dev'
            }
            steps {
                script {
                    kubernetesDeploy(
                        configs: 'backend/deployment/kubernetes/*.yaml',
                        kubeConfig: [path: env.KUBECONFIG_DEV],
                        enableConfigSubstitution: true,
                        secretNamespace: env.NAMESPACE
                    )

                    // Wait for deployment
                    sh """
                        kubectl wait --for=condition=available --timeout=300s \\
                            deployment/heatguard-api -n ${NAMESPACE}
                    """

                    // Health check
                    sleep 30
                    sh """
                        kubectl port-forward service/heatguard-api-service 8080:8000 -n ${NAMESPACE} &
                        sleep 5
                        curl -f http://localhost:8080/api/v1/health
                    """
                }
            }
        }

        stage('Deploy to Staging') {
            when {
                anyOf {
                    branch 'main'
                    params.DEPLOY_ENVIRONMENT == 'staging'
                }
            }
            environment {
                KUBECONFIG = "${KUBECONFIG_STAGING}"
                NAMESPACE = 'heatguard-staging'
            }
            steps {
                script {
                    kubernetesDeploy(
                        configs: 'backend/deployment/kubernetes/*.yaml',
                        kubeConfig: [path: env.KUBECONFIG_STAGING],
                        enableConfigSubstitution: true,
                        secretNamespace: env.NAMESPACE
                    )

                    // Wait and verify
                    sh """
                        kubectl wait --for=condition=available --timeout=300s \\
                            deployment/heatguard-api -n ${NAMESPACE}

                        sleep 30
                        curl -f https://api-staging.heatguard.com/api/v1/health
                    """
                }
            }
        }

        stage('Deploy to Production') {
            when {
                anyOf {
                    branch 'main'
                    params.DEPLOY_ENVIRONMENT == 'production'
                }
            }
            environment {
                KUBECONFIG = "${KUBECONFIG_PROD}"
                NAMESPACE = 'heatguard'
            }
            steps {
                // Manual approval for production
                script {
                    def deployApproved = false
                    try {
                        timeout(time: 10, unit: 'MINUTES') {
                            deployApproved = input(
                                message: 'Deploy to Production?',
                                ok: 'Deploy',
                                submitterParameter: 'APPROVER',
                                parameters: [
                                    choice(
                                        name: 'DEPLOYMENT_STRATEGY',
                                        choices: ['blue-green', 'rolling'],
                                        description: 'Deployment strategy'
                                    )
                                ]
                            )
                        }
                    } catch (err) {
                        deployApproved = false
                    }

                    if (deployApproved) {
                        echo "Production deployment approved by: ${APPROVER}"

                        if (params.DEPLOYMENT_STRATEGY == 'blue-green') {
                            // Blue-Green deployment
                            sh """
                                cd backend/deployment/kubernetes

                                # Create green deployment
                                sed -i "s|name: heatguard-api|name: heatguard-api-green|g" deployment.yaml
                                sed -i "s|image: heatguard/api:.*|image: ${FULL_IMAGE_NAME}|g" deployment.yaml

                                kubectl apply -f deployment.yaml --kubeconfig=${KUBECONFIG}
                                kubectl wait --for=condition=available --timeout=600s \\
                                    deployment/heatguard-api-green -n ${NAMESPACE} --kubeconfig=${KUBECONFIG}

                                # Health check green deployment
                                kubectl port-forward deployment/heatguard-api-green 8080:8000 -n ${NAMESPACE} --kubeconfig=${KUBECONFIG} &
                                sleep 10
                                curl -f http://localhost:8080/api/v1/health

                                # Switch traffic to green
                                kubectl patch service heatguard-api-service -n ${NAMESPACE} --kubeconfig=${KUBECONFIG} \\
                                    -p '{"spec":{"selector":{"app.kubernetes.io/name":"heatguard-api-green"}}}'

                                # Verify production
                                sleep 30
                                curl -f https://api.heatguard.com/api/v1/health

                                # Clean up old deployment
                                kubectl delete deployment heatguard-api -n ${NAMESPACE} --kubeconfig=${KUBECONFIG} || true
                            """
                        } else {
                            // Rolling update
                            kubernetesDeploy(
                                configs: 'backend/deployment/kubernetes/*.yaml',
                                kubeConfig: [path: env.KUBECONFIG_PROD],
                                enableConfigSubstitution: true,
                                secretNamespace: env.NAMESPACE
                            )
                        }
                    } else {
                        error("Production deployment not approved")
                    }
                }
            }
        }

        stage('Post-Deployment Tests') {
            when {
                anyOf {
                    branch 'main'
                    params.DEPLOY_ENVIRONMENT == 'production'
                }
            }
            parallel {
                stage('Smoke Tests') {
                    steps {
                        script {
                            docker.image("python:${PYTHON_VERSION}").inside() {
                                dir('backend/tests') {
                                    sh '''
                                        pip install requests pytest
                                        python production_smoke_tests.py
                                    '''
                                }
                            }
                        }
                    }
                }

                stage('Performance Monitoring') {
                    steps {
                        script {
                            docker.image("python:${PYTHON_VERSION}").inside() {
                                dir('backend/tests') {
                                    sh '''
                                        pip install requests numpy matplotlib
                                        python performance_benchmarks.py --environment=production
                                    '''
                                }
                            }
                        }

                        archiveArtifacts(
                            artifacts: 'backend/tests/performance-results.json',
                            allowEmptyArchive: true
                        )
                    }
                }
            }
        }

        stage('Monitoring Setup') {
            when {
                branch 'main'
            }
            steps {
                script {
                    sh """
                        cd backend/deployment/monitoring
                        kubectl apply -f prometheus.yml --kubeconfig=${KUBECONFIG_PROD}
                        kubectl apply -f grafana-dashboard.json --kubeconfig=${KUBECONFIG_PROD}
                        kubectl apply -f alerts.yml --kubeconfig=${KUBECONFIG_PROD}
                    """
                }
            }
        }
    }

    post {
        always {
            // Clean up workspace
            cleanWs(
                cleanWhenNotBuilt: false,
                deleteDirs: true,
                disableDeferredWipeout: true,
                notFailBuild: true
            )

            // Archive build artifacts
            archiveArtifacts(
                artifacts: 'backend/**/*-report.*',
                allowEmptyArchive: true,
                fingerprint: true
            )
        }

        success {
            slackSend(
                channel: '#heatguard-ci',
                color: 'good',
                message: ":white_check_mark: HeatGuard pipeline succeeded for ${env.BRANCH_NAME} - Build #${env.BUILD_NUMBER}\\n" +
                         "Image: `${FULL_IMAGE_NAME}`\\n" +
                         "Deploy Environment: ${params.DEPLOY_ENVIRONMENT}"
            )
        }

        failure {
            slackSend(
                channel: '#heatguard-ci',
                color: 'danger',
                message: ":x: HeatGuard pipeline failed for ${env.BRANCH_NAME} - Build #${env.BUILD_NUMBER}\\n" +
                         "Check: ${env.BUILD_URL}"
            )
        }

        unstable {
            slackSend(
                channel: '#heatguard-ci',
                color: 'warning',
                message: ":warning: HeatGuard pipeline unstable for ${env.BRANCH_NAME} - Build #${env.BUILD_NUMBER}"
            )
        }
    }
}