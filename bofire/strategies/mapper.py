from typing import Dict, Type

import bofire.data_models.strategies.api as data_models
from bofire.strategies.predictives.botorch import BotorchStrategy  # noqa: F401
from bofire.strategies.predictives.predictive import PredictiveStrategy  # noqa: F401
from bofire.strategies.predictives.qehvi import QehviStrategy  # noqa: F401
from bofire.strategies.predictives.qnehvi import QnehviStrategy  # noqa: F401
from bofire.strategies.predictives.qparego import QparegoStrategy  # noqa: F401
from bofire.strategies.predictives.sobo import (  # noqa: F401
    AdditiveSoboStrategy,
    MultiplicativeSoboStrategy,
    SoboStrategy,
)
from bofire.strategies.random import RandomStrategy  # noqa: F401
from bofire.strategies.samplers.polytope import PolytopeSampler  # noqa: F401
from bofire.strategies.samplers.rejection import RejectionSampler  # noqa: F401
from bofire.strategies.samplers.sampler import SamplerStrategy  # noqa: F401
from bofire.strategies.strategy import Strategy  # noqa: F401

STRATEGY_MAP: Dict[Type[data_models.Strategy], Type[Strategy]] = {
    data_models.RandomStrategy: RandomStrategy,
    data_models.SoboStrategy: SoboStrategy,
    data_models.AdditiveSoboStrategy: AdditiveSoboStrategy,
    data_models.MultiplicativeSoboStrategy: MultiplicativeSoboStrategy,
    data_models.QehviStrategy: QehviStrategy,
    data_models.QnehviStrategy: QnehviStrategy,
    data_models.QparegoStrategy: QparegoStrategy,
    data_models.PolytopeSampler: PolytopeSampler,
    data_models.RejectionSampler: RejectionSampler,
}


def map(data_model: data_models.Strategy) -> Strategy:
    cls = STRATEGY_MAP[data_model.__class__]
    return cls.from_spec(data_model=data_model)