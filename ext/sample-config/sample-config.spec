Name:           QVD-default-config
Version:        3.1.0
Release:        %{_svn_rev}
Summary:        QVD Default config
License:        unknown
Group:          Development/Libraries
URL:            http://svn.int.qindel.com/repos/main/projects/qindel/QVD/src/trunk/ext/sample-config
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildArch:      noarch
BuildRequires:  qvd-common-libs
Requires:       perl-QVD-L7R
Requires:       perl-QVD-HKD
Requires:       perl-QVD-Config
Requires:       perl-QVD-DB
Requires:       postgresql-server
Vendor:         QVD Team

%description
QVD default config

%prep
mkdir -p $RPM_BUILD_DIR
cd $RPM_BUILD_DIR
svn co -r %{_svn_rev} http://svn.int.qindel.com/repos/main/projects/qindel/QVD/src/trunk/ext/sample-config



%build

%install

cd $RPM_BUILD_DIR/sample-config
rm -rf $RPM_BUILD_ROOT

mkdir -p "$RPM_BUILD_ROOT/etc/qvd"
mkdir -p "$RPM_BUILD_ROOT/usr/lib/qvd/bin"

cp node.conf "$RPM_BUILD_ROOT/etc/qvd"
cp qvd-sample-init.sh "$RPM_BUILD_ROOT/usr/lib/qvd/bin"


%clean
rm -rf $RPM_BUILD_ROOT


%post

hostname=`hostname`
gateway=`ip -o route | grep '^default' | awk '{print $3}'`

export PATH=/usr/lib/qvd/bin:/bin:/usr/bin:/sbin:/usr/sbin
set -e -x


if [ ! -f /etc/qvd/server-private-key.pem -o ! -f /etc/qvd/server-certificate.pem ] ; then
	openssl genrsa 1024 > /etc/qvd/server-private-key.pem

	cat >/etc/qvd/server-certificate.cnf <<SSL_CONF
RANDFILE               = $ENV{HOME}/.rnd
[ req ]
default_bits           = 1024
default_keyfile        = /etc/qvd/server-private-key.pem
distinguished_name     = req_distinguished_name
attributes             = req_attributes
prompt                 = no
output_password        =

[ req_distinguished_name ]
C                      = ES
ST                     = Madrid
L                      = Madrid
O                      = QVD Test
OU                     = QVD
CN                     = QVD Test
emailAddress           = test@example.com
[ req_attributes ]
challengePassword      =

SSL_CONF

	openssl req -new -x509 -nodes -sha1 -days 60 -key /etc/qvd/server-private-key.pem -config /etc/qvd/server-certificate.cnf -out /etc/qvd/server-certificate.pem

	set_cert=1
fi

### Edit config
sed -i "s/^nodename =.*/nodename = $hostname/g" "/etc/qvd/node.conf"
sed -i "s/^vm.network.gateway =.*/vm.network.gateway = $gateway/g" "/etc/qvd/node.conf"

### Start postgres
if ( ! /etc/init.d/postgresql status ) ; then
	/etc/init.d/postgresql start
fi

### Edit config if needed
if ( ! grep -q '^# QVD Settings' /var/lib/pgsql/data/pg_hba.conf )  ; then

	cat >/var/lib/pgsql/data/pg_hba.conf <<CONF
# database or username with that name.
#
# This file is read on server startup and when the postmaster receives
# a SIGHUP signal.  If you edit the file on a running system, you have
# to SIGHUP the postmaster for the changes to take effect.  You can use
# "pg_ctl reload" to do that.

# Put your actual configuration here
# ----------------------------------
#
# If you want to allow non-local connections, you need to add more
# "host" records. In that case you will also need to make PostgreSQL listen
# on a non-local interface via the listen_addresses configuration parameter,
# or via the -i or -h command line switches.
#



# TYPE  DATABASE    USER        CIDR-ADDRESS          METHOD

# QVD Settings - do not remove or change this line
host    qvd         qvd         ::1/128               md5
host    qvd         qvd         127.0.0.1/32          md5

# "local" is for Unix domain socket connections only
local   all         all                               ident sameuser
# IPv4 local connections:
host    all         all         127.0.0.1/32          ident sameuser
# IPv6 local connections:
host    all         all         ::1/128               ident sameuser

CONF

	/etc/init.d/postgresql restart
fi

# Create DB
if ( ! su - postgres -c "psql -l" | grep -E -q '^\s+qvd ' ) ; then
	echo -e "qvd\nqvd" | su -  postgres -c "createuser -e -S -D -R -E -P qvd"
	su -  postgres -c "createdb -E UTF8 -O qvd qvd"
	db_created=1
fi

# Init DB
if [ -n "$db_created" -o ! -f /etc/qvd/.db_initialized ] ; then
	/usr/lib/qvd/bin/qvd-sample-init.sh && touch /etc/qvd/.db_initialized
fi

# Set cert, if one was generated before
if [ -n "$set_cert" -o -z "`qvd-admin.pl config get l7r.ssl.key`" ] ; then
	qvd-admin.pl config ssl key=/etc/qvd/server-private-key.pem cert=/etc/qvd/server-certificate.pem
fi

%files
/*

%changelog
* Tue Dec 13 2011 Qindel 3.1.0
- Specfile autogenerated by build.pl 0.1.
