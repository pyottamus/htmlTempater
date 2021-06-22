import piScoper
import tageater
import re
import collections
import functools
import sys
import os
import subprocess
import tcSTD
class bind():
    def __init__(self, func, *args):
        self._func=func
        self._args=args
        
    def __call__(self, *args):
        y=list(self._args) + list(args)
        self._func(*y)


class templaterSetInterceptStartCommand:
    def __init__(self, name, command):
        self.name=name
        self.command=command
    def __call__(self, target):
        target.pushInterceptStart(self.name, self.command)
        return lambda : target.popInterceptStart(self.name)
class templaterSetInterceptStartEndCommand:
    def __init__(self, name, command):
        self.name=name
        self.command=command
    def __call__(self, target):
        target.pushInterceptStartEnd(self.name, self.command)
        return lambda : target.popInterceptStartEnd(self.name)


class psuedoTemplate():
    def __init__(self, target):
        self.target=target
        self.history=[]
    def __call__(self):
        [x() for x in self.history]
    def excecute(self, command):
        self.history.append(command(self.target))
    def setInterceptStart(self, name, command):
        self.excecute(templaterSetInterceptStartCommand(name, command))
    def setInterceptStartEnd(self, name, command):
        self.excecute(templaterSetInterceptStartEndCommand(name, command))
    def out(self, string):
        self.target.outFile+=string
class templater():
    def __init__(self, string):
        self.outFile=""
        self.parser = piScoper.PIscoper()
        self.parser.appenddat(string)
        self.tcDEFTAGsearchdir="./DEFTAG_INC"
        self.tcInterceptStart=collections.defaultdict(list)
        self.tcInterceptStartEnd=collections.defaultdict(list)
        
        self.intermode=False

        self.piTypes=["TC"]
        self.parser.addDescopeHandler(self.piDescope)
        self.parser.addScopeHandler(self.piScope)
        self.parser.addHandler(tageater.startTag, self.tagStart)
        self.parser.addHandler(tageater.endTag, self.tagEnd)
        self.parser.addHandler(tageater.textTag, self.handleText)
        self.parser.addHandler(tageater.selfClosingTag, self.tagStartEnd)
        self.parser.addHandler(tageater.cdataTag, self.cdata)
        self.parser.addHandler(tageater.doctypeTag, self.doctype)
        self.tcStack=[]#list of tc command destructors

     
        
    def intermodeHandler(self, tag):
        self.tcFuncAssosiations[self.tcTag.name][-1][1](tag)
       
        
    def intermodeExec(self):
        rep=self.tcFuncAssosiations[self.tcTag.name][-1]
        rep[0](rep[2])
        self.tcTag=None
        self.intermodeFile=""
        self.intermode=False
    def piScope(self, tag):
        self.tcStack.append(psuedoTemplate(self))
        if tag.target in self.piTypes:
            tcSTD.TC(self.tcStack[-1], tag)
        else:
            self.outFile+=tag.raw
        
    def piDescope(self, tag):
        self.tcStack.pop()()
    def pushInterceptStart(self, name, command):
        self.tcInterceptStart[name].append(command)
        
    def pushInterceptStartEnd(self, name, command):
        self.tcInterceptStartEnd[name].append(command)

    def popInterceptStart(self, name):
        self.tcInterceptStart[name].pop()
        
    def popInterceptStartEnd(self, name):
        self.tcInterceptStartEnd[name].pop()
    def tagStart(self, tag):
        
        """
        Process start tag.
        May trager intermode
        Will not triger intermodeExec
        """
        if self.intermode==False:
            if len(self.tcInterceptStart[tag.name])>0:#if tag is special to tc
                self.tcInterceptStart[tag.name][-1](tag)
                return
            
            else:
                self.outFile+=tag.raw#not special. add to raw
        else:
            if tag.name==self.tcTag.name:#increase depth so that closing tag wont end intermode
                self.tcDepth+=1
            self.intermodeHandler(tag)#handle intermode

    def tagStartEnd(self, tag):
        """
        Handles self closing tag.
        Will not trigger intermode
        May triger intermodeExec
        """
        if self.intermode==False:
            if len(self.tcInterceptStartEnd[tag.name])>0:

                self.tcInterceptStartEnd[tag.name][-1](tag)
                return
            else:
                self.outFile+=tag.raw
        else:
            self.intermodeHandler(tag)

    def tagEnd(self, tag):
        """
        Handles closing tag
        Will not triger intermode
        May triger tcExec
        May be called from implicit tag close
        """
        if self.intermode==False:
            self.outFile+=tag.raw
        else:
            if tag.name==self.tcTag.name:
                self.tcDepth-=1

            if self.tcDepth==0:
                self.intermodeExec()
            else:
                self.intermodeHandler(tag)
    def cdata(self, tag):
        if self.intermode==False:
            self.outFile+=tag.raw
        else:
            self.intermodeHandler(tag)
    def doctype(self, tag):
        if self.intermode==False:
            self.outFile+=tag.raw
        else:
            raise RuntimeError("Encontered doctype during intermode")
    def handleText(self, tag):
        """
        Handles Text
        Will not triger intermode
        WIll not triger tcExec
        """
        if self.intermode==False:
            self.outFile+=tag.raw
        else:
            self.intermodeHandler(tag)
    


if __name__=="__main__":
    name=sys.argv[1]
    #name="test.php"
    with open(name) as x:
        y=templater(x.read())

    y.parser.start()
    dirPath=os.path.dirname(os.path.abspath(name))
    outFile=os.path.splitext(os.path.basename(name))[0]+".php"
    outDir=os.path.join(dirPath, outFile)
    
    with open(outDir, "w") as x:
        x.write(y.outFile)

