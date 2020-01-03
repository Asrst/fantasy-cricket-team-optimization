## Fantasy Cricket Team Selection - Optimization using Linear Programming.


### requirements
1. pandas
2. pulp

if pulp is not installed:
use `pip install pulp` to install

### run
`python optimize_team.py -p \path\to\csv`

- outputs a csv `solution.csv` with 11 optimal players in the `/files/` folder
- for sample format of csv: refer `files/usecase_player.csv` file


### references
- https://blog.remix.com/an-intro-to-integer-programming-for-engineers-simplified-bus-scheduling-bd3d64895e92
- https://towardsdatascience.com/linear-programming-and-discrete-optimization-with-python-using-pulp-449f3c5f6e99