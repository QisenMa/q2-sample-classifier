#!/usr/bin/env python

# ----------------------------------------------------------------------------
# Copyright (c) 2017--, q2-sample-classifier development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------


from sklearn.ensemble import (RandomForestRegressor, RandomForestClassifier,
                              ExtraTreesClassifier, ExtraTreesRegressor,
                              AdaBoostClassifier, GradientBoostingClassifier,
                              AdaBoostRegressor, GradientBoostingRegressor)
from sklearn.metrics import mean_squared_error
from sklearn.svm import LinearSVC, SVR, SVC
from sklearn.linear_model import Ridge, Lasso, ElasticNet
from sklearn.pipeline import Pipeline
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor

import qiime2
import biom
from scipy.stats import randint
import warnings

from .utilities import (split_optimize_classify, visualize, load_data,
                        tune_parameters)


ensemble_params = {"max_depth": [4, 8, 16, None],
                   "max_features": [None, 'sqrt', 'log2', 0.1],
                   "min_samples_split": [0.001, 0.01, 0.1],
                   "min_weight_fraction_leaf": [0.0001, 0.001, 0.01],
                   "bootstrap": [True, False]}


linear_svm_params = {"C": [1, 0.5, 0.1, 0.9, 0.8],
                     # should probably include penalty in grid search, but:
                     # Unsupported set of arguments: The combination of
                     # penalty='l1' and loss='hinge' is not supported
                     # "penalty": ["l1", "l2"],
                     "loss": ["hinge", "squared_hinge"],
                     "tol": [0.00001, 0.0001, 0.001]
                     # should probably include this in grid search, as
                     # dual=False is preferred when samples>features. However:
                     # Unsupported set of arguments: The combination of
                     # penalty='l2' and loss='hinge' are not supported when
                     # dual=False
                     # "dual": [True, False]
                     }


svm_params = {"C": [1, 0.5, 0.1, 0.9, 0.8],
              "tol": [0.00001, 0.0001, 0.001, 0.01],
              "shrinking": [True, False]}


neighbors_params = {
    "n_neighbors": randint(2, 15),
    "weights": ['uniform', 'distance'],
    "leaf_size": randint(15, 100)
}


linear_params = {
    "alpha": [0.0001, 0.01, 1.0, 10.0, 1000.0],
    "tol": [0.00001, 0.0001, 0.001, 0.01]
}


def classify_random_forest(output_dir: str, table: biom.Table,
                           metadata: qiime2.Metadata, category: str,
                           test_size: float=0.2, step: float=0.05,
                           cv: int=5, random_state: int=None, n_jobs: int=1,
                           n_estimators: int=100,
                           optimize_feature_selection: bool=False,
                           parameter_tuning: bool=False):

    # specify parameters and distributions to sample from for parameter tuning
    param_dist = {**ensemble_params, "criterion": ["gini", "entropy"]}

    estimator = RandomForestClassifier(
        n_jobs=n_jobs, n_estimators=n_estimators)

    estimator, cm, accuracy, importances = split_optimize_classify(
        table, metadata, category, estimator, output_dir,
        test_size=test_size, step=step, cv=cv, random_state=random_state,
        n_jobs=n_jobs, optimize_feature_selection=optimize_feature_selection,
        parameter_tuning=parameter_tuning, param_dist=param_dist,
        calc_feature_importance=True)

    visualize(output_dir, estimator, cm, accuracy, importances,
              optimize_feature_selection)


def classify_extra_trees(output_dir: str, table: biom.Table,
                         metadata: qiime2.Metadata, category: str,
                         test_size: float=0.2, step: float=0.05,
                         cv: int=5, random_state: int=None, n_jobs: int=1,
                         n_estimators: int=100,
                         optimize_feature_selection: bool=False,
                         parameter_tuning: bool=False):

    # specify parameters and distributions to sample from for parameter tuning
    param_dist = {**ensemble_params, "criterion": ["gini", "entropy"]}

    estimator = ExtraTreesClassifier(
        n_jobs=n_jobs, n_estimators=n_estimators)

    estimator, cm, accuracy, importances = split_optimize_classify(
        table, metadata, category, estimator, output_dir,
        test_size=test_size, step=step, cv=cv, random_state=random_state,
        n_jobs=n_jobs, optimize_feature_selection=optimize_feature_selection,
        parameter_tuning=parameter_tuning, param_dist=param_dist,
        calc_feature_importance=True)

    visualize(output_dir, estimator, cm, accuracy, importances,
              optimize_feature_selection)


def classify_adaboost(output_dir: str, table: biom.Table,
                      metadata: qiime2.Metadata, category: str,
                      test_size: float=0.2, step: float=0.05,
                      cv: int=5, random_state: int=None, n_jobs: int=1,
                      n_estimators: int=100,
                      optimize_feature_selection: bool=False,
                      parameter_tuning: bool=False):

    base_estimator = DecisionTreeClassifier()

    # specify parameters and distributions to sample from for parameter tuning
    param_dist = {k: ensemble_params[k] for k in ensemble_params.keys()
                  if k != "bootstrap"}

    # parameter tune base estimator
    if parameter_tuning:
        features, targets = load_data(table, metadata, transpose=True)
        base_estimator = tune_parameters(
            features, targets[category], base_estimator, param_dist,
            n_jobs=n_jobs, cv=cv, random_state=random_state)

    estimator = AdaBoostClassifier(base_estimator, n_estimators)

    estimator, cm, accuracy, importances = split_optimize_classify(
        table, metadata, category, estimator, output_dir,
        test_size=test_size, step=step, cv=cv, random_state=random_state,
        n_jobs=n_jobs, optimize_feature_selection=optimize_feature_selection,
        parameter_tuning=False, param_dist=param_dist,
        calc_feature_importance=True)

    visualize(output_dir, estimator, cm, accuracy, importances,
              optimize_feature_selection)


def classify_gradient_boosting(output_dir: str, table: biom.Table,
                               metadata: qiime2.Metadata, category: str,
                               test_size: float=0.2, step: float=0.05,
                               cv: int=5, random_state: int=None,
                               n_jobs: int=1, n_estimators: int=100,
                               optimize_feature_selection: bool=False,
                               parameter_tuning: bool=False):

    # specify parameters and distributions to sample from for parameter tuning
    param_dist = {k: ensemble_params[k] for k in ensemble_params.keys()
                  if k != "bootstrap"}

    estimator = GradientBoostingClassifier(n_estimators=n_estimators)

    estimator, cm, accuracy, importances = split_optimize_classify(
        table, metadata, category, estimator, output_dir,
        test_size=test_size, step=step, cv=cv, random_state=random_state,
        n_jobs=n_jobs, optimize_feature_selection=optimize_feature_selection,
        parameter_tuning=parameter_tuning, param_dist=param_dist,
        calc_feature_importance=True)

    visualize(output_dir, estimator, cm, accuracy, importances,
              optimize_feature_selection)


def regress_random_forest(output_dir: str, table: biom.Table,
                          metadata: qiime2.Metadata, category: str,
                          test_size: float=0.2, step: float=0.05,
                          cv: int=5, random_state: int=None, n_jobs: int=1,
                          n_estimators: int=100,
                          optimize_feature_selection: bool=False,
                          parameter_tuning: bool=False):

    # specify parameters and distributions to sample from for parameter tuning
    param_dist = ensemble_params

    estimator = RandomForestRegressor(n_jobs=n_jobs, n_estimators=n_estimators)

    estimator, cm, accuracy, importances = split_optimize_classify(
        table, metadata, category, estimator, output_dir,
        test_size=test_size, step=step, cv=cv, random_state=random_state,
        n_jobs=n_jobs, optimize_feature_selection=optimize_feature_selection,
        parameter_tuning=parameter_tuning, param_dist=param_dist,
        calc_feature_importance=True, scoring=mean_squared_error,
        classification=False)

    visualize(output_dir, estimator, cm, accuracy, importances,
              optimize_feature_selection)


def regress_extra_trees(output_dir: str, table: biom.Table,
                        metadata: qiime2.Metadata, category: str,
                        test_size: float=0.2, step: float=0.05,
                        cv: int=5, random_state: int=None, n_jobs: int=1,
                        n_estimators: int=100,
                        optimize_feature_selection: bool=False,
                        parameter_tuning: bool=False):

    # specify parameters and distributions to sample from for parameter tuning
    param_dist = ensemble_params

    estimator = ExtraTreesRegressor(n_jobs=n_jobs, n_estimators=n_estimators)

    estimator, cm, accuracy, importances = split_optimize_classify(
        table, metadata, category, estimator, output_dir,
        test_size=test_size, step=step, cv=cv, random_state=random_state,
        n_jobs=n_jobs, optimize_feature_selection=optimize_feature_selection,
        parameter_tuning=parameter_tuning, param_dist=param_dist,
        calc_feature_importance=True, scoring=mean_squared_error,
        classification=False)

    visualize(output_dir, estimator, cm, accuracy, importances,
              optimize_feature_selection)


def regress_adaboost(output_dir: str, table: biom.Table,
                     metadata: qiime2.Metadata, category: str,
                     test_size: float=0.2, step: float=0.05,
                     cv: int=5, random_state: int=None, n_jobs: int=1,
                     n_estimators: int=100,
                     optimize_feature_selection: bool=False,
                     parameter_tuning: bool=False):

    base_estimator = DecisionTreeRegressor()

    # specify parameters and distributions to sample from for parameter tuning
    param_dist = {k: ensemble_params[k] for k in ensemble_params.keys()
                  if k != "bootstrap"}

    # parameter tune base estimator
    if parameter_tuning:
        features, targets = load_data(table, metadata, transpose=True)
        base_estimator = tune_parameters(
            features, targets[category], base_estimator, param_dist,
            n_jobs=n_jobs, cv=cv, random_state=random_state)

    estimator = AdaBoostRegressor(base_estimator, n_estimators)

    estimator, cm, accuracy, importances = split_optimize_classify(
        table, metadata, category, estimator, output_dir,
        test_size=test_size, step=step, cv=cv, random_state=random_state,
        n_jobs=n_jobs, optimize_feature_selection=optimize_feature_selection,
        parameter_tuning=False, param_dist=param_dist,
        calc_feature_importance=True, scoring=mean_squared_error,
        classification=False)

    visualize(output_dir, estimator, cm, accuracy, importances,
              optimize_feature_selection)


def regress_gradient_boosting(output_dir: str, table: biom.Table,
                              metadata: qiime2.Metadata, category: str,
                              test_size: float=0.2, step: float=0.05,
                              cv: int=5, random_state: int=None,
                              n_jobs: int=1, n_estimators: int=100,
                              optimize_feature_selection: bool=False,
                              parameter_tuning: bool=False):

    # specify parameters and distributions to sample from for parameter tuning
    param_dist = {k: ensemble_params[k] for k in ensemble_params.keys()
                  if k != "bootstrap"}

    estimator = GradientBoostingRegressor(n_estimators=n_estimators)

    estimator, cm, accuracy, importances = split_optimize_classify(
        table, metadata, category, estimator, output_dir,
        test_size=test_size, step=step, cv=cv, random_state=random_state,
        n_jobs=n_jobs, optimize_feature_selection=optimize_feature_selection,
        parameter_tuning=parameter_tuning, param_dist=param_dist,
        calc_feature_importance=True, scoring=mean_squared_error,
        classification=False)

    visualize(output_dir, estimator, cm, accuracy, importances,
              optimize_feature_selection)


def classify_linearSVC(output_dir: str, table: biom.Table,
                       metadata: qiime2.Metadata, category: str,
                       test_size: float=0.2, step: float=0.05,
                       cv: int=5, random_state: int=None, n_jobs: int=1,
                       parameter_tuning: bool=False,
                       optimize_feature_selection: bool=False):

    # specify parameters and distributions to sample from for parameter tuning
    param_dist = linear_svm_params

    estimator = LinearSVC()

    estimator, cm, accuracy, importances = split_optimize_classify(
        table, metadata, category, estimator, output_dir,
        test_size=test_size, step=step, cv=cv, random_state=random_state,
        n_jobs=n_jobs, optimize_feature_selection=optimize_feature_selection,
        parameter_tuning=parameter_tuning, param_dist=param_dist,
        calc_feature_importance=True)

    visualize(output_dir, estimator, cm, accuracy, importances,
              optimize_feature_selection)


def classify_SVC(output_dir: str, table: biom.Table,
                 metadata: qiime2.Metadata, category: str,
                 test_size: float=0.2, step: float=0.05,
                 cv: int=5, random_state: int=None, n_jobs: int=1,
                 parameter_tuning: bool=False,
                 optimize_feature_selection: bool=False, kernel: str='rbf'):

    # specify parameters and distributions to sample from for parameter tuning
    param_dist = svm_params

    estimator = SVC(kernel=kernel)

    # linear SVC returns feature weights as coef_
    calc_feature_importance, optimize_feature_selection = svm_set(
        kernel, optimize_feature_selection)

    estimator, cm, accuracy, importances = split_optimize_classify(
        table, metadata, category, estimator, output_dir,
        test_size=test_size, step=step, cv=cv, random_state=random_state,
        n_jobs=n_jobs, optimize_feature_selection=optimize_feature_selection,
        parameter_tuning=parameter_tuning, param_dist=param_dist,
        calc_feature_importance=calc_feature_importance)

    visualize(output_dir, estimator, cm, accuracy, importances,
              optimize_feature_selection)


def regress_SVR(output_dir: str, table: biom.Table,
                metadata: qiime2.Metadata, category: str,
                test_size: float=0.2, step: float=0.05,
                cv: int=5, random_state: int=None, n_jobs: int=1,
                parameter_tuning: bool=False,
                optimize_feature_selection: bool=False, kernel: str='rbf'):

    # specify parameters and distributions to sample from for parameter tuning
    param_dist = {**svm_params, 'epsilon': [0.0, 0.1]}

    estimator = SVR(kernel=kernel)

    # linear SVR returns feature weights as coef_ , non-linear does not
    calc_feature_importance, optimize_feature_selection = svm_set(
        kernel, optimize_feature_selection)

    estimator, cm, accuracy, importances = split_optimize_classify(
        table, metadata, category, estimator, output_dir,
        test_size=test_size, step=step, cv=cv, random_state=random_state,
        n_jobs=n_jobs, optimize_feature_selection=optimize_feature_selection,
        parameter_tuning=parameter_tuning, param_dist=param_dist,
        calc_feature_importance=calc_feature_importance,
        scoring=mean_squared_error, classification=False)

    visualize(output_dir, estimator, cm, accuracy, importances,
              optimize_feature_selection)


def regress_ridge(output_dir: str, table: biom.Table,
                  metadata: qiime2.Metadata, category: str,
                  test_size: float=0.2, step: float=0.05,
                  cv: int=5, random_state: int=None, n_jobs: int=1,
                  parameter_tuning: bool=False,
                  optimize_feature_selection: bool=False, solver: str='auto'):

    # specify parameters and distributions to sample from for parameter tuning
    param_dist = linear_params

    estimator = Ridge(solver=solver)

    estimator, cm, accuracy, importances = split_optimize_classify(
        table, metadata, category, estimator, output_dir,
        test_size=test_size, step=step, cv=cv, random_state=random_state,
        n_jobs=n_jobs, optimize_feature_selection=optimize_feature_selection,
        parameter_tuning=parameter_tuning, param_dist=param_dist,
        calc_feature_importance=True, scoring=mean_squared_error,
        classification=False)

    visualize(output_dir, estimator, cm, accuracy, importances,
              optimize_feature_selection)


def regress_lasso(output_dir: str, table: biom.Table,
                  metadata: qiime2.Metadata, category: str,
                  test_size: float=0.2, step: float=0.05,
                  cv: int=5, random_state: int=None, n_jobs: int=1,
                  optimize_feature_selection: bool=False,
                  parameter_tuning: bool=False):

    # specify parameters and distributions to sample from for parameter tuning
    param_dist = linear_params

    estimator = Lasso()

    estimator, cm, accuracy, importances = split_optimize_classify(
        table, metadata, category, estimator, output_dir,
        test_size=test_size, step=step, cv=cv, random_state=random_state,
        n_jobs=n_jobs, optimize_feature_selection=optimize_feature_selection,
        parameter_tuning=parameter_tuning, param_dist=param_dist,
        calc_feature_importance=True, scoring=mean_squared_error,
        classification=False)

    visualize(output_dir, estimator, cm, accuracy, importances,
              optimize_feature_selection)


def regress_elasticnet(output_dir: str, table: biom.Table,
                       metadata: qiime2.Metadata, category: str,
                       test_size: float=0.2, step: float=0.05,
                       cv: int=5, random_state: int=None, n_jobs: int=1,
                       optimize_feature_selection: bool=False,
                       parameter_tuning: bool=False):

    # specify parameters and distributions to sample from for parameter tuning
    param_dist = linear_params

    estimator = ElasticNet()

    estimator, cm, accuracy, importances = split_optimize_classify(
        table, metadata, category, estimator, output_dir,
        test_size=test_size, step=step, cv=cv, random_state=random_state,
        n_jobs=n_jobs, optimize_feature_selection=optimize_feature_selection,
        parameter_tuning=parameter_tuning, param_dist=param_dist,
        calc_feature_importance=True, scoring=mean_squared_error,
        classification=False)

    visualize(output_dir, estimator, cm, accuracy, importances,
              optimize_feature_selection)


def classify_kneighbors(output_dir: str, table: biom.Table,
                        metadata: qiime2.Metadata, category: str,
                        test_size: float=0.2, step: float=0.05,
                        cv: int=5, random_state: int=None, n_jobs: int=1,
                        parameter_tuning: bool=False, algorithm: str='auto'):

    # specify parameters and distributions to sample from for parameter tuning
    param_dist = neighbors_params

    estimator = KNeighborsClassifier(algorithm=algorithm)

    estimator, cm, accuracy, importances = split_optimize_classify(
        table, metadata, category, estimator, output_dir,
        test_size=test_size, step=step, cv=cv, random_state=random_state,
        n_jobs=n_jobs, optimize_feature_selection=False,
        parameter_tuning=parameter_tuning, param_dist=param_dist,
        calc_feature_importance=False)

    visualize(output_dir, estimator, cm, accuracy, importances, False)


def regress_kneighbors(output_dir: str, table: biom.Table,
                       metadata: qiime2.Metadata, category: str,
                       test_size: float=0.2, step: float=0.05,
                       cv: int=5, random_state: int=None, n_jobs: int=1,
                       parameter_tuning: bool=False, algorithm: str='auto'):

    # specify parameters and distributions to sample from for parameter tuning
    param_dist = neighbors_params

    estimator = KNeighborsRegressor(algorithm=algorithm)

    estimator, cm, accuracy, importances = split_optimize_classify(
        table, metadata, category, estimator, output_dir,
        test_size=test_size, step=step, cv=cv, random_state=random_state,
        n_jobs=n_jobs, optimize_feature_selection=False,
        parameter_tuning=parameter_tuning, param_dist=param_dist,
        calc_feature_importance=False, scoring=mean_squared_error,
        classification=False)

    visualize(output_dir, estimator, cm, accuracy, importances, False)


# Need to figure out how to pickle/import estimators
def classify_new_data(table: biom.Table, estimator: Pipeline):
    '''Use trained estimator to predict values on unseen data.'''
    predictions = estimator.predict(table)
    return predictions


def svm_set(kernel, optimize_feature_selection):
    if kernel == 'linear':
        calc_feature_importance = True
        optimize_feature_selection = optimize_feature_selection
    else:
        calc_feature_importance = False
        optimize_feature_selection = False
        warn_feature_selection()
    return calc_feature_importance, optimize_feature_selection


def warn_feature_selection():
    warning = (
        ('This estimator does not support recursive feature extraction with '
         'the parameter settings requested. See documentation or try a '
         'different estimator model.'))
    warnings.warn(warning, UserWarning)
