# main.py
import numpy as np
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

import xgboost as xgb
import torch
import sys


def test_sklearn():
    print("=== scikit-learn RandomForest ===")
    X, y = load_iris(return_X_y=True)
    clf = RandomForestClassifier(n_estimators=50, random_state=42)
    clf.fit(X, y)
    preds = clf.predict(X)
    acc = accuracy_score(y, preds)
    print("RandomForestClassifier accuracy on Iris:", acc)
    if acc < 0.9:
        raise RuntimeError("scikit-learn test failed!")


def test_xgboost():
    print("\n=== XGBoost ===")
    X, y = load_iris(return_X_y=True)
    dtrain = xgb.DMatrix(X, label=y)
    params = {"objective": "multi:softmax", "num_class": 3, "max_depth": 3, "eta": 0.3}
    bst = xgb.train(params, dtrain, num_boost_round=20)
    preds = bst.predict(dtrain)
    acc = (preds == y).mean()
    print("XGBoost accuracy on Iris:", acc)
    if acc < 0.9:
        raise RuntimeError("XGBoost test failed!")


def test_torch():
    print("\n=== PyTorch ===")
    x = torch.randn(5, 3)
    w = torch.randn(3, 2, requires_grad=True)
    y = x @ w
    loss = y.sum()
    loss.backward()
    print("Input:", x.shape, "Weights:", w.shape, "Output:", y.shape)
    print("Gradients on weights:", w.grad.shape)


if __name__ == "__main__":
    try:
        test_sklearn()
        test_xgboost()
        test_torch()
        print("\n✅ All libraries are working correctly.")
    except Exception as e:
        print("\n❌ Test failed:", e)
        sys.exit(1)

