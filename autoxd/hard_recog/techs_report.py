#coding:utf8

class techs_report(object):
    def __init__(self, codes):
        self.codes = codes
        
    def run(self, fn ):
        """
        r = run(pl, codes)
        """
        pl = publish.Publish(is_clear_path=True)
        
        codes = self.codes
        pl.myimgs += "<table>"
        for code in codes:
            pl.myimgs += "<tr><td><table>"
            try:
                fn(pl, code)
            except:
                pass
            pl.myimgs += "</table></td></tr>"
        pl.myimgs += "</table>"
        pl.publish()    
        
        
if __name__ == "__main__":
    techs_report().run()
    