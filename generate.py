import subprocess

for x in range(50, 51):
    fileName = 'generated/level' + str(x).zfill(2) + '.dat'
    result = subprocess.run(['python3', 'main.py', '1000', '3001'], stdout=subprocess.PIPE)
    with open(fileName, "wb") as f:
        f.write(result.stdout)
        f.close()
