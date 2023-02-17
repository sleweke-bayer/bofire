import pytest

from bofire.domain.feature import (
    CategoricalDescriptorInput,
    ContinuousInput,
    ContinuousOutput,
)
from bofire.domain.features import InputFeatures, OutputFeatures
from bofire.models.gps import SingleTaskGPModel
from bofire.utils.enum import CategoricalEncodingEnum


@pytest.mark.parametrize("folds", [5, 3, 10, -1])
def test_model_cross_validate(folds):
    input_features = InputFeatures(
        features=[
            ContinuousInput(key=f"x_{i+1}", lower_bound=-4, upper_bound=4)
            for i in range(2)
        ]
    )
    output_features = OutputFeatures(features=[ContinuousOutput(key="y")])
    experiments = input_features.sample(n=100)
    experiments.eval("y=((x_1**2 + x_2 - 11)**2+(x_1 + x_2**2 -7)**2)", inplace=True)
    experiments["valid_y"] = 1
    experiments = experiments.sample(10)
    model = SingleTaskGPModel(
        input_features=input_features,
        output_features=output_features,
    )
    train_cv, test_cv, _ = model.cross_validate(experiments, folds=folds)
    efolds = folds if folds != -1 else 10
    assert len(train_cv.results) == efolds
    assert len(test_cv.results) == efolds


def test_model_cross_validate_descriptor():
    folds = 5
    input_features = InputFeatures(
        features=[
            ContinuousInput(key=f"x_{i+1}", lower_bound=-4, upper_bound=4)
            for i in range(2)
        ]
        + [
            CategoricalDescriptorInput(
                key="x_3",
                categories=["a", "b", "c"],
                descriptors=["alpha"],
                values=[[1], [2], [3]],
            )
        ]
    )
    output_features = OutputFeatures(features=[ContinuousOutput(key="y")])
    experiments = input_features.sample(n=100)
    experiments.eval("y=((x_1**2 + x_2 - 11)**2+(x_1 + x_2**2 -7)**2)", inplace=True)
    experiments.loc[experiments.x_2 == "b", "y"] += 5
    experiments.loc[experiments.x_2 == "c", "y"] += 10
    experiments["valid_y"] = 1
    experiments = experiments.sample(10)
    for encoding in [
        CategoricalEncodingEnum.ONE_HOT,
        CategoricalEncodingEnum.DESCRIPTOR,
    ]:
        model = SingleTaskGPModel(
            input_features=input_features,
            output_features=output_features,
            input_preprocessing_specs={"x_3": encoding},
        )
        train_cv, test_cv, _ = model.cross_validate(experiments, folds=folds)
        efolds = folds if folds != -1 else 10
        assert len(train_cv.results) == efolds
        assert len(test_cv.results) == efolds


@pytest.mark.parametrize("include_X", [True, False])
def test_model_cross_validate_include_X(include_X):
    input_features = InputFeatures(
        features=[
            ContinuousInput(key=f"x_{i+1}", lower_bound=-4, upper_bound=4)
            for i in range(2)
        ]
    )
    output_features = OutputFeatures(features=[ContinuousOutput(key="y")])
    experiments = input_features.sample(n=10)
    experiments.eval("y=((x_1**2 + x_2 - 11)**2+(x_1 + x_2**2 -7)**2)", inplace=True)
    experiments["valid_y"] = 1
    model = SingleTaskGPModel(
        input_features=input_features,
        output_features=output_features,
    )
    train_cv, test_cv, _ = model.cross_validate(
        experiments, folds=5, include_X=include_X
    )
    if include_X:
        assert train_cv.results[0].X.shape == (8, 2)
        assert test_cv.results[0].X.shape == (2, 2)
    if include_X is False:
        assert train_cv.results[0].X is None
        assert test_cv.results[0].X is None


def test_model_cross_validate_hooks():
    def hook1(model, X_train, y_train, X_test, y_test):
        assert isinstance(model, SingleTaskGPModel)
        assert y_train.shape == (8, 1)
        assert y_test.shape == (2, 1)
        return X_train.shape

    def hook2(model, X_train, y_train, X_test, y_test, return_test=True):
        if return_test:
            return X_test.shape
        return X_train.shape

    input_features = InputFeatures(
        features=[
            ContinuousInput(key=f"x_{i+1}", lower_bound=-4, upper_bound=4)
            for i in range(2)
        ]
    )
    output_features = OutputFeatures(features=[ContinuousOutput(key="y")])
    experiments = input_features.sample(n=10)
    experiments.eval("y=((x_1**2 + x_2 - 11)**2+(x_1 + x_2**2 -7)**2)", inplace=True)
    experiments["valid_y"] = 1
    #
    model = SingleTaskGPModel(
        input_features=input_features,
        output_features=output_features,
    )
    # first test with one hook
    _, _, hook_results = model.cross_validate(
        experiments, folds=5, hooks={"hook1": hook1}
    )
    assert len(hook_results.keys()) == 1
    assert len(hook_results["hook1"]) == 5
    assert hook_results["hook1"] == [(8, 2), (8, 2), (8, 2), (8, 2), (8, 2)]
    # now test with two hooks
    _, _, hook_results = model.cross_validate(
        experiments, folds=5, hooks={"hook1": hook1, "hook2": hook2}
    )
    assert len(hook_results.keys()) == 2
    assert len(hook_results["hook1"]) == 5
    assert hook_results["hook1"] == [(8, 2), (8, 2), (8, 2), (8, 2), (8, 2)]
    assert len(hook_results["hook2"]) == 5
    assert hook_results["hook2"] == [(2, 2), (2, 2), (2, 2), (2, 2), (2, 2)]
    # now test with two hooks and keyword arguments
    _, _, hook_results = model.cross_validate(
        experiments,
        folds=5,
        hooks={"hook1": hook1, "hook2": hook2},
        hook_kwargs={"hook2": {"return_test": False}},
    )
    assert len(hook_results.keys()) == 2
    assert len(hook_results["hook1"]) == 5
    assert hook_results["hook1"] == [(8, 2), (8, 2), (8, 2), (8, 2), (8, 2)]
    assert len(hook_results["hook2"]) == 5
    assert hook_results["hook2"] == [(8, 2), (8, 2), (8, 2), (8, 2), (8, 2)]


@pytest.mark.parametrize("folds", [-2, 0, 1, 11])
def test_model_cross_validate_invalid(folds):
    input_features = InputFeatures(
        features=[
            ContinuousInput(key=f"x_{i+1}", lower_bound=-4, upper_bound=4)
            for i in range(2)
        ]
    )
    output_features = OutputFeatures(features=[ContinuousOutput(key="y")])
    experiments = input_features.sample(n=10)
    experiments.eval("y=((x_1**2 + x_2 - 11)**2+(x_1 + x_2**2 -7)**2)", inplace=True)
    experiments["valid_y"] = 1
    model = SingleTaskGPModel(
        input_features=input_features,
        output_features=output_features,
    )
    with pytest.raises(ValueError):
        model.cross_validate(experiments, folds=folds)