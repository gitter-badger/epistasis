import inspect
import numpy as np
from .additive import AdditiveSimulation
from .multiplicative import MultiplicativeSimulation
from .base import BaseSimulation
from epistasis.models.nonlinear.model import Parameters

class NonlinearSimulation(BaseSimulation):
    """ Nonlinear epistasis simulator. Creates a Genotype-Phen
    """
    def __init__(self, wildtype, mutations, order,
            function,
            p0,
            coeff_range=(-1,1),
            model_type='local',
            linear_model=None,
            multiplicative=False,
        ):
        # Set the linear piece of epistasis map.
        if linear_model is not None:
            self.linear = linear_model
        else:
            if multiplicative:
                # Linear epistasis map
                self.linear = MultiplicativeSimulation(wildtype, mutations, order,
                    coeff_range=coeff_range,
                    model_type=model_type)
            else:
                self.linear = AdditiveSimulation(wildtype, mutations, order,
                    coeff_range=coeff_range,
                    model_type=model_type)

        # Set the nonlinear function
        self.function = function

        # Construct GPM
        super(NonlinearSimulation, self).__init__(
            self.linear.wildtype,
            self.linear.mutations,
        )
        # Get the parameters from the nonlinear function argument list
        function_sign = inspect.signature(self.function)
        parameters = list(function_sign.parameters.keys())

        # Check that the first argument is epistasis
        if parameters[0] != "x":
            raise Exception("""First argument of the nonlinear function must be `x`.""")

        #Set parameters
        self.parameters = Parameters(parameters[1:])
        for i in range(1, len(parameters)):
            self.parameters._set_param(parameters[i], p0[i-1])

        # Build phenotypes.
        self.build()

    @property
    def p_additive(self):
        """Get the additive phenotype"""
        return self.function(self.linear.p_additive, *self.parameters.get_params())

    @classmethod
    def from_linear(cls, model, function, p0):
        """Layer nonlinear model on top of existing linear model."""
        return cls(model.wildtype,
            model.mutations,
            model.epistasis.order,
            function,
            p0,
            linear_model=model)

    def build(self, *args):
        """ Build nonlinear map from epistasis and function.
        """
        self.phenotypes = self.function(self.linear.phenotypes, *self.parameters.values)

    def widget(self, **kwargs):
        """ A widget for playing with different values of nonlinearity. """
        pass
