.PHONY: clean

SRC_DOCS := $(shell ls *.txt)

# Uncomment this line to produce HTML docs from all the available text files in
# this directory.
#HTML_DOCS := $(subst .txt,.html,${SRC_DOCS})
HTML_DOCS := howto-using_remote_controller.html
#RST2HTML := rst2html -t --stylesheet-path=nuxeo_doc.css 
RST2HTML := rst2html -t --stylesheet-path=default.css 

all: ${HTML_DOCS}

%.html: %.txt
	${RST2HTML} $< $@


%.toc: %.txt
	grep -B1 -e "==" $<  | grep -v "==" | grep -v "\-\-" |  sed "s/^\(.*\)/* \`\1\`_/g"


clean:
	rm -f *~
	rm -f ${HTML_DOCS}
