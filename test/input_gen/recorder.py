#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
##
# Copyright (C) 2020 Jihoon Lee <jhoon.it.lee@samsung.com>
#
# @file recorder.py
# @date 13 October 2020
# @brief Generate tc from given keras model
# @author Jihoon lee <jhoon.it.lee@samsung.com>

from functools import wraps
import sys
import os
import warnings
import random
from collections import defaultdict

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=FutureWarning)
    import numpy as np
    import tensorflow as tf
    from tensorflow.python import keras as K

from transLayer import attach_trans_layer, MultiOutLayer

__all__ = ["record"]

tf.compat.v1.enable_eager_execution()
# Fix the seeds across frameworks
SEED = 1234
random.seed(SEED)
tf.compat.v1.set_random_seed(SEED)
np.random.seed(SEED)

LOSS_FN = {
    "mse": lambda: tf.keras.losses.MeanSquaredError(),
    "cross_sigmoid": lambda: tf.keras.losses.BinaryCrossentropy(from_logits=True),
    "cross_softmax": lambda: tf.keras.losses.CategoricalCrossentropy(from_logits=True),
}


def _flatten(l: list):
    for el in l:
        if isinstance(el, list):
            yield from _flatten(el)
        else:
            yield el


def _get_loss_fn(loss_fn_representation):
    try:
        return LOSS_FN[loss_fn_representation]()
    except KeyError:
        raise ValueError("given loss fn representation is not available")


def _get_writer(file):
    def write_fn(*items):
        for item in items:
            try:
                item.numpy().tofile(file)
            except AttributeError:
                pass
        return items

    return write_fn


def _rand_like(tensorOrShape, scale=1):
    try:
        shape = tensorOrShape.shape
    except AttributeError:
        shape = tensorOrShape

    t = np.random.randint(-10, 10, shape).astype(dtype=np.float32)
    return tf.convert_to_tensor(t) * scale


##
# @brief access keras layer hidden inside a tensor
# @note this function is relying on non-api implementation, this might break in the future
# @param tensor tensor to get layer
def _klayer(tensor):
    return tensor._keras_history.layer


_debug_default_formatter = lambda key, value: "\033[4;32mkey: {}\033[0m\n {}".format(
    key, value
)
##
# @brief Print debug information from the record
# @param debug list or string that filters debug information from @a data
# @param print_option print option for the print function
# @param print_format print formatter. a callable that takes key and value should be passed
# @param data data to passed to _debug_print
def _debug_print(
    debug=None,
    print_option={"end": "\n"},
    print_format=_debug_default_formatter,
    **data
):
    if not debug:
        return
    elif isinstance(debug, str):
        debug = [debug]

    for target in debug:
        try:
            print(print_format(target, data[target]), **print_option)
        except KeyError:
            pass


##
# @brief generate data using uniform data from a function and save to the file.
# @note one-hot label is supported for now, this could be extended if needed.
def prepare_data(model, input_shape, label_shape, writer_fn, is_onehot, **kwargs):
    initial_input = _rand_like(input_shape) / 10
    if is_onehot:
        label = tf.one_hot(
            indices=np.random.randint(0, label_shape[1] - 1, label_shape[0]),
            depth=label_shape[1],
        )
    else:
        label=_rand_like(label_shape) / 10

    initial_weights = []
    for layer in iter_model(model):
        if "file_shape_generation" in kwargs.get("debug", []):
            get_shape = lambda x: [i.shape for i in x]
            print(layer.name)
            print("initial_weights", get_shape(layer.weights))
        initial_weights += layer.weights.copy()

    writer_fn(initial_input, label, *initial_weights)
    _debug_print(
        initial_input=initial_input,
        label=label,
        initial_weights=initial_weights,
        **kwargs
    )

    return initial_input, label


##
# @brief iterate model in the order of output rather than layer
# @note we might need a bit of reordering if output is more than one, this is assuming 1 to 1 mapping of a model and they are far apart
# @param model model to be iterated
# @yield layer
def iter_model(model):
    for out in model.outputs:
        yield _klayer(out)


##
# @brief model iteration wrapper that listen to the gradient and outputs of the model
# each results are recorded.
def train_step(model, optimizer, loss_fn, initial_input, label, writer_fn, **kwargs):
    with tf.GradientTape(persistent=True) as tape:
        tape.watch(initial_input)

        inp = initial_input
        outp = model.call(inp, training=True)
        outputs = {}
        inputs = {}
        for layer in model.layers:
            output_indices = model.recorder__output_map[layer.name]
            outputs[layer.name] = [outp[i] for i in output_indices]

            input_indices = model.recorder__input_map[layer.name]
            inputs[layer.name] = [outp[i] for i in input_indices]

        loss = loss_fn(label, outp[-1])

    for layer in iter_model(model):

        if isinstance(layer, MultiOutLayer):
            continue

        layer_output = outputs[layer.name]
        layer_input = inputs[layer.name]

        # when there is a multiple input, this will break.
        if not layer_input:
            layer_input = [initial_input]

        gradients = tape.gradient(loss, layer.trainable_weights)
        # if layer.name == 'target':
            # print(tape.gradient(loss, layer.hi))
        optimizer.apply_gradients(zip(gradients, layer.trainable_weights))

        if isinstance(optimizer, tf.keras.optimizers.Adam):
            wm = [optimizer.get_slot(var, "m") for var in layer.trainable_weights]
            wv = [optimizer.get_slot(var, "v") for var in layer.trainable_weights]
            _debug_print(wm=wm, wv=wv, **kwargs)

        _debug_print(lr=optimizer.lr, **kwargs)

        weights = layer.weights.copy()
        dx = tape.gradient(loss, list(_flatten(layer_input)))

        try:
            gradients = layer.to_nntr_trainable_weights(gradients)
        except AttributeError:
            pass

        writer_fn(
            *layer_output,  # output of forward
            *dx,  # output of backward
            *gradients,  # weight gradient output from backward
            *weights  # updated weight after optimization
        )

        _debug_print(name=layer.name, print_format=value_only_formatter, **kwargs)

        if "file_shape_generation" in kwargs.get("debug", []):
            get_shape = lambda x: [i.shape for i in x]
            print(layer.name)
            print("output", get_shape(layer_output))
            print("dx", get_shape(dx))
            print("weights", get_shape(weights))
            print("gradients", get_shape(gradients))

        _debug_print(
            output=layer_output,
            dx=dx,
            weights=weights,
            gradients=gradients,
            dx_shape=[i.shape for i in dx],
            **kwargs
        )

    writer_fn(loss)
    _debug_print(loss=loss, **kwargs)


##
# @brief inference_step of the result
def inference_step(loss_fn_str, initial_input, label, writer_fn):
    # Not yet implemented
    # because loss function with fromLogit is used, last layer fc layer should be added for the inference step
    if loss_fn_str == "cross_sigmoid" or loss_fn_str == "cross_entropy":
        # add last activation layer
        pass
    raise NotImplementedError("Not Implemented yet")


value_only_formatter = lambda key, value: value

##
# @brief generate recordable model
# @note if model, inputs, outputs is given, trans_layer will NOT be automatically attached
# @note in case of using multiout layer, output usage order must match
# @param loss_fn_str one of LOSS_FN string otherwise raise KeyError
# @param model base model to record, if model is present @a inputs and @a outputs is ignored
# @param inputs keras inputs to build a model
# @param outputs keras outputs to build a model
def generate_recordable_model(
    loss_fn_str, model=None, inputs=None, outputs=None, is_onehot=False, **kwargs
):
    if isinstance(model, list):
        model = [attach_trans_layer(layer) for layer in model]

        inputs = model[0]  # first layer must be input
        outputs = [inputs]
        for layer in model[1:]:
            current_output = layer(outputs[-1])
            outputs.append(current_output)

    if isinstance(model, K.models.Model) == False:
        # omit last activation layer if cross softmax or cross_sigmoid
        if loss_fn_str == "cross_softmax" or loss_fn_str == "cross_sigmoid":
            if isinstance(_klayer(outputs[-1]), K.layers.Activation):
                outputs = outputs[:-1]

        model = K.Model(inputs=inputs, outputs=outputs)

    inputs = model.inputs
    outputs = model.outputs

    model.summary(
        print_fn=lambda x: _debug_print(
            summary=x, print_format=value_only_formatter, **kwargs
        )
    )

    output_map = {}
    for idx, output in enumerate(model.outputs):
        layer_name = _klayer(output).name
        try:
            output_map[layer_name].append(idx)
        except KeyError:
            output_map[layer_name] = [idx]

    input_map = defaultdict(list)

    def _insert_input_map(key_layer):
        if isinstance(key_layer, K.layers.InputLayer):
            return

        input_node = key_layer.input

        if not isinstance(input_node, list):
            input_node = [input_node]

        for node in input_node:
            layer, _, tensor_idx = node._keras_history

            target_idx = output_map[layer.name][tensor_idx]
            input_list = input_map[key_layer.name]
            if target_idx not in input_list:
                input_list.append(target_idx)

    for idx, output in enumerate(outputs):
        target_layer = model.get_layer(_klayer(output).name)
        _insert_input_map(target_layer)

    for _, value in input_map.items():
        if not value:
            raise ValueError(f"input_map must contain value. {input_map}")

    _debug_print(input_map=input_map, output_map=output_map, **kwargs)

    # Additional property of output, inputs. This maps index of outputs which
    # will be used to locate the calculated output
    # same applies to model input
    # eg) if in model(inputs=A, outputs=[A, B]),
    # if B is output of A, output_map[_klayer(B).name] will have 0 (index of A)
    model.recorder__output_map = output_map
    model.recorder__input_map = input_map

    return model


##
# @brief record function that records weights, gradients, inputs and outputs for @a iteration
# @param loss_fn_str loss function representation
# @param optimizer keras optimizer
# @param file_name file name to save
# @param input_shape input shape to put
# @param label_shape label shape to put
# @param iteration number of iteration to run
# @param model base model to record, if model is present @a inputs and @a outputs is ignored
# @param inputs keras inputs to build a model
# @param outputs keras outputs to build a model
# @param debug a single string key or list of keys to print out particular information,
# checkout usage of _debug_print of which is printed. for example `_debug_print(loss=loss, **kwargs)`
# catches debug="loss" or debug=["loss"] to print out loss
def record(
    loss_fn_str,
    optimizer,
    file_name,
    input_shape,
    label_shape,
    iteration=1,
    model=None,
    inputs=None,
    outputs=None,
    is_onehot=True,
    **kwargs
):
    if os.path.isfile(file_name):
        print("Warning: the file %s is being truncated and overwritten" % file_name)

    loss_fn = _get_loss_fn(loss_fn_str)
    model = generate_recordable_model(loss_fn_str, model, inputs, outputs, is_onehot, **kwargs)

    with open(file_name, "wb") as f:
        write = _get_writer(f)

        initial_input, label = prepare_data(
            model, input_shape, label_shape, write, is_onehot, **kwargs
        )
        for _ in range(iteration):
            _debug_print(
                iteration="\033[1;33m[%d/%d]\033[0m" % (_ + 1, iteration),
                print_format=value_only_formatter,
                **kwargs
            )
            train_step(model, optimizer, loss_fn, initial_input, label, write, **kwargs)

        # self.inference_step(initial_input, label, write)
