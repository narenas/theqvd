QVDCLIENTDIR=../../c
QVDCLIENTWRAPPER=../libqvdclientwrapper

default: all

all android: 
	mvn install -Dmaven.test.skip=true

test:
	mvn test

clean:
	mvn clean
	rm -f *.log *~

distclean: clean

.EXPORT_ALL_VARIABLES:
