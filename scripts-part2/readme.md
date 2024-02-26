## scripts-part2

#### Usage:

- `local-parta.sh`: script for parta. It will perform tests and log results automatically.
  - `./local-parta.sh`
    - make sure config repo `cloud-comp-arch-project` and this repo are at the same directory
    - the test will take more than 20min

- `local-partb.sh`: script for partb. It will perform tests and log results automatically.

  - `./local-partb.sh`
    - make sure config repo `cloud-comp-arch-project` and this repo are at the same directory
    - the test will take more than 20min

- `report.py`: python data analysis for part a and b

  - `python3 report.py <part name>`:

    - i.e. `python3 report.py a`, output will be like:

      ```shell
      							cpu		l1d		l1i		l2		llc		membw	none
      blackscholes	1.231	1.283	1.515	1.273	1.39	1.286	1.0
      canneal				1.039	1.201	1.796	1.17	1.795	1.264	1.0
      dedup					1.149	0.804	1.439	0.875	1.438	1.112	1.0
      ferret				1.868	1.071	2.193	1.156	2.649	2.051	1.0
      freqmine			1.999	1.014	1.99	1.012	1.791	1.569	1.0
      radix					1.015	1.107	1.08	1.215	1.537	1.085	1.0
      vips					1.739	1.639	1.829	1.632	1.982	1.714	1.0
      ```

      