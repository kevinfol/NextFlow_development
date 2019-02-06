def readConfig(key):
    with open('resources/application_prefs.ini', 'r') as readFile:
        fileContents = readFile.readlines()
        for line in fileContents:
            if key in line:
                value = line.split('=')[1].strip('\n')
                value = value.strip(' ')
                break
    return value