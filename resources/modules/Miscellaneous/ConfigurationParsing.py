def readConfig(key):
    with open('resources/application_prefs.ini', 'r') as readFile:
        fileContents = readFile.readlines()
        for line in fileContents:
            if key in line:
                value = line.split('=')[1].strip('\n')
                value = value.strip(' ')
                break
    return value

def writeConfig(key, value):
    with open('resources/application_prefs.ini', 'r') as readFile:
        fileContents = readFile.readlines()
        for i, line in enumerate(fileContents):
            if key in line:
                fileContents[i] = key+'='+str(value)+'\n'
                break
    with open('resources/application_prefs.ini', 'w') as writeFile:
        writeFile.writelines(fileContents)
    return 

def readUserOptions(key):
    with open('resources/temp/user_set_options.txt', 'r') as readFile:
        fileContents = readFile.readlines()
        for line in fileContents:
            if key in line:
                value = line.split('=')[1].strip('\n')
                value = value.strip(' ')
                break
    return value

def writeUserOptions(key, value):
    if key == 'current_map_location':
        print('writing location')
    with open('resources/temp/user_set_options.txt', 'r') as readFile:
        fileContents = readFile.readlines()
        for i, line in enumerate(fileContents):
            if key in line:
                fileContents[i] = key+'='+str(value)+'\n'
                break
        
    with open('resources/temp/user_set_options.txt', 'w') as writeFile:
        writeFile.writelines(fileContents)
    return 