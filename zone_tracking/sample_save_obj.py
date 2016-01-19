import os

if not os.path.exists('../model'):
    os.mkdir('../model')
from sklearn import svm
from sklearn import datasets

clf = svm.SVC()
iris = datasets.load_iris()
X, y = iris.data, iris.target
clf.fit(X, y)
print clf.predict(X[0:5])
from sklearn.externals import joblib

joblib.dump(clf, '../model/filename.pkl')
clf = joblib.load('../model/filename.pkl')
print clf.predict(X[0:5])
