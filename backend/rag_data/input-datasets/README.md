# Knowledge-base corpus

Drop source documents here. The loader reads `.pdf`, `.txt`, and `.md`.

Suggested contents (10-20 documents is plenty for MS2):

- Research papers on converter / inverter fault diagnosis (open-circuit and
  short-circuit switch faults, DC-link capacitor degradation, gate-driver
  failures, sensor faults). Download the PDF, name it `paper_<n>_<topic>.pdf`.
- Manufacturer datasheets and application notes for IGBT / SiC MOSFET modules
  and gate drivers (Infineon, Wolfspeed, Semikron, TI all publish these freely).
- Maintenance or failure-analysis guides for the converter topology your
  dataset came from.

Keep file names short and descriptive; the file name is what the assistant
cites in its answers.

`sample_fault_primer.txt` is a short seed document so the pipeline runs before
you add real papers. Delete it once the real corpus is in place.
