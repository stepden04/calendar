from datetime import datetime
from typing import List
from json import load,dumps

class Course:
    time: datetime
    day: str
    leap: int
    name: str
    teacher: str 
    link: str 
    note: str
    def __init__(self,
                 time: str,
                 day: str,
                 leap: int,
                 name: str,
                 teacher: str,
                 link: str,
                 note: str) -> None:
        self.time = time
        self.day = day
        self.leap = leap
        self.name = name
        self.teacher = teacher
        self.link = link
        self.note = note

    def toJSON(self):
        return dumps(self, default=lambda o: o.__dict__, 
                sort_keys=True, indent=4)

    def __str__(self) -> str:
        br = '\n'
        return f"{self.time} - {self.name} ({self.teacher}){f'{br}!{self.note}' if self.note!=None else ''}"
    
    def full(self) -> str:
        br = '\n'
        return f"{self.day}|{self.leap}\n{self.time} - {self.name} ({self.teacher}){f'{br}!{self.note}' if self.note!=None else ''}"

    def get_link(self) -> str:
        return self.link

    def __repr__(self) -> str:
        return self.__str__()
    
def isLeap(line : str):
    if line.find('|') != -1:
        return int(line[line.find('|')+1])-1
    else:
        return 2

def get_note(str:str):
    if str.find('(') != -1:
        return str[str.find('(')+1:-1]

def chunks(lst, n): #вкрав
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def clear(list : List[str]):
    return [x for x in list if x]

def load_cache():
    jsonFile = open("cache.json", "r")
    data = load(jsonFile)
    jsonFile.close()
    return data

def save_cache(cache_dict):
    #jsonString = dumps(cache_dict)
    jsonFile = open("cache.json", "w")
    jsonFile.write(dumps(cache_dict,default=vars))
    jsonFile.close()

def read_msg(text) -> list[Course]:
    course_list = []
    
    for num,day in enumerate(text.split("——————————————————")):
        
        day = clear(day.split('\n'))[1:]
        
        classes = list(chunks(day,4))

        for n,course in enumerate(classes):
            if course[2].lower() != 'вікно':
                course_list.append( Course(
                time = course[0][:5],
                day = num,
                leap = isLeap(course[0]),
                name = course[2][1:-1],
                teacher = course[1],
                link = course[3],
                note = get_note(course[0]))
            )
                                      
        # for i,msg in enumerate(clear(day.split('\n'))[1:]):
        #     print(i,msg)
    return course_list
