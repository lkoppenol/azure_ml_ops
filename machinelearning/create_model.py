from sklearn.datasets import load_iris
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
import pickle


def get_model():
    iris = load_iris()
    x = iris.data
    y = iris.target

    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.33, random_state=42)

    clf = DecisionTreeClassifier() \
        .fit(x_train, y_train)

    score = clf.score(x_test, y_test)
    print(f"Trained model with score {score}")
    return clf


if __name__ == "__main__":
    model = get_model()

    with open('model.pkl', 'wb') as handle:
        pickle.dump(model, handle)
