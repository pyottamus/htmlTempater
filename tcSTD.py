import tageater
import re
import collections
#Handles incoming TC. Works as a factory
def TC(templater, tag):
    coms={"REPLTAG":REPLTAG}
    x=re.search("([a-zA-Z]+)\s(.*)", tag.instruction)
    if x==None:
        raise RuntimeError()
    function=x.group(1).upper()
    dat=x.group(2)
    return coms[function](templater, tag, function, dat)
        
class REPLTAG:
    def __init__(self, templater, tag, function, dat):
        self.templater=templater
        self.dat=""
        self.name=""
        
        self.nameSearch=re.compile("^<([a-zA-Z\-]+)")
        self.attSearch=x=re.compile("(\\S+)=[\"']?((?:.(?![\"']?\\s+(?:\\S+)=|[>\"']))+.)[\"']?")
        self.inside=""
        self.function=function
        self.dat=dat
        self.name=self.nameSearch.search(self.dat).group(1)
      
        self.templater.setInterceptStart(self.name, self.REPLTAG_inter)
        self.templater.setInterceptStartEnd(self.name, self.REPLTAG_startend)


    def REPLTAG_inter(self, tag):
        self.dat+=tag.raw        
    def REPLTAG_startend(self, tag):
        self.dat+=tag.raw
        
        self.REPLTAG()
    def repParse(self, com, inDict):
        out=""
        rem=re.search("<"+self.name+">(.*?)</"+self.name+">", com).group(1)
        left=re.search("(.*?)\$\{\{([a-zA-Z\-]*)\}\}(.*)", rem)
        while left!=None:
            out+=left.group(1)
            out+=inDict[left.group(2)]
            rem=left.group(3)
            left=re.search("(.*?)\$\{\{([a-zA-Z\-]*)\}\}(.*)", rem)
        out+=rem
        return out 
    def REPLTAG(self):  
        atrDict=collections.defaultdict(str)
        pos=0
        res=self.attSearch.search(self.dat, pos)
        while res!=None:
            
            atrDict[res.group(1)]=res.group(2)
            pos+=res.endpos
            res=self.attSearch.search(self.dat, pos)
        self.templater.out(self.repParse(self.dat, atrDict))
        self.dat=""
