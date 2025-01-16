# HAQA
HAQA is a hardware-guided and fidelity-aware strategy for efficient qubit mapping optimization and can be used in multiple solver-based mapping methods.
This repository contains HAQA's main code.

![recursive-community-fusion](https://github.com/user-attachments/assets/e6a2bfb3-6a0e-432a-bd44-dbe4409fdc0f)


The main contribution of HAQA is:
1. HAQA introduced a hardware-oriented region identification mechanism
   A community-based iterative region identification strategy is developed in HAQA, leveraging quantum hardware connectivity to reduce mapping space dimensionality and avoid global search processes.

2. HAQA proposed a hardware-characteristic-based region evaluation mechanism
   HAQA eables quantitative selection of mapping regions based on fidelity metrics, addressing the limitations of existing solvers in considering hardware fidelity characteristics.

3. HAQA demonstrated polynomial-level acceleration potential
   HAQA provides computational complexity analysis showing significant theoretical acceleration in qubit mapping processes while adapting to increasingly complex quantum hardware architectures.
