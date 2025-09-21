export interface PredictionInput {
  Temperature: number;
  Humidity: number;
  hrv_mean_hr?: number;
  hrv_rmssd?: number;
  Gender?: number;
  Age?: number;
  [key: string]: number | string | boolean | undefined;
}

export interface PredictionResult {
  risk_score: number;
  predicted_class: string;
  confidence: number;
  error?: string;
}

class JSModelLoader {
  private isLoaded = false;

  async predict(input: PredictionInput): Promise<PredictionResult> {
    try {
      // For now, create a mock prediction based on temperature and humidity
      // In a real implementation, this would load and use an actual ML model
      const { Temperature, Humidity } = input;

      // Simple risk calculation based on temperature and humidity
      const heatIndex = this.calculateHeatIndex(Temperature, Humidity);

      let risk_score: number;
      let predicted_class: string;
      let confidence: number;

      if (heatIndex >= 105) {
        risk_score = 0.9;
        predicted_class = "HIGH_RISK";
        confidence = 0.85;
      } else if (heatIndex >= 90) {
        risk_score = 0.6;
        predicted_class = "MODERATE_RISK";
        confidence = 0.75;
      } else if (heatIndex >= 80) {
        risk_score = 0.3;
        predicted_class = "LOW_RISK";
        confidence = 0.65;
      } else {
        risk_score = 0.1;
        predicted_class = "MINIMAL_RISK";
        confidence = 0.70;
      }

      // Add some randomness for demo purposes
      const randomFactor = 0.9 + Math.random() * 0.2;
      risk_score = Math.min(1.0, risk_score * randomFactor);
      confidence = Math.min(1.0, confidence * (0.95 + Math.random() * 0.1));

      return {
        risk_score: Number(risk_score.toFixed(3)),
        predicted_class,
        confidence: Number(confidence.toFixed(3))
      };

    } catch (error) {
      return {
        risk_score: 0,
        predicted_class: "ERROR",
        confidence: 0,
        error: error instanceof Error ? error.message : 'Unknown prediction error'
      };
    }
  }

  private calculateHeatIndex(tempF: number, humidity: number): number {
    // Convert Celsius to Fahrenheit if needed (assuming input might be in Celsius)
    const temperature = tempF > 50 ? tempF : (tempF * 9/5) + 32;

    if (temperature < 80) {
      return temperature;
    }

    // Simplified heat index calculation
    const hi = -42.379 +
               2.04901523 * temperature +
               10.14333127 * humidity -
               0.22475541 * temperature * humidity -
               6.83783e-3 * temperature * temperature -
               5.481717e-2 * humidity * humidity +
               1.22874e-3 * temperature * temperature * humidity +
               8.5282e-4 * temperature * humidity * humidity -
               1.99e-6 * temperature * temperature * humidity * humidity;

    return hi;
  }

  get loaded(): boolean {
    return this.isLoaded;
  }
}

export const jsModelLoader = new JSModelLoader();