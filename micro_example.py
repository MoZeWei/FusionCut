import os, math
import os, logging

logging.disable(logging.WARNING)
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "1"
# Comment this line if using GPU
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

# from cutqc_runtime.main import CutQC # Use this just to benchmark the runtime

from cutqc.main import CutQC # Use this for exact computation

from helper_functions.benchmarks import generate_circ

if __name__ == "__main__":
    circuit_type = "MICRO"
    circuit_size = 10
    circuit = generate_circ(
        num_qubits=circuit_size,
        depth=1,
        circuit_type=circuit_type,
        reg_name="q",
        connected_only=True,
        seed=None,
    )
    cutqc = CutQC(
        name="%s_%d" % (circuit_type, circuit_size),
        circuit=circuit,
        cutter_constraints={
            "max_subcircuit_width": math.ceil(circuit.num_qubits / 4 * 3),
            "max_subcircuit_cuts": 10,
            "subcircuit_size_imbalance": 2,
            "max_cuts": 10,
            "num_subcircuits": [2],
        },
        verbose=True,
    )
    cutqc.cut()
    print("Finish the cutting")
    exit(1)
    if not cutqc.has_solution:
        raise Exception("The input circuit and constraints have no viable cuts")

    cutqc.evaluate(eval_mode="sv", num_shots_fn=None)
    cutqc.build(mem_limit=32, recursion_depth=1)
    print("Cut: %d recursions." % (cutqc.num_recursions))
    print(cutqc.approximation_bins)
    cutqc.clean_data()
