package QVD::L7R::Authenticator;

use strict;
use warnings;

use QVD::Config;
use QVD::Log;
use Carp;

my $case_sensitive_login = cfg('model.user.login.case-sensitive');

my @plugin_modules;
for (split /\s*,\s*/, cfg('l7r.auth.plugins')) {
    s/^\s+//;
    s/\s+$//;
    /^\w+$/ or croak "bad plugin name $_";
    s/^(.)/uc $1/e;
    my $module = "QVD::L7R::Authenticator::Plugin::$_";
    eval "require $module; 1"
        or croak "unable to load $module: $@";
    push @plugin_modules, $module;
}

sub new {
    my $class = shift;
    my $auth = { modules => [@plugin_modules],
                 params  => {},
                 login   => undef,
                 user_id => undef };
    bless $auth, $class;
    $_->init($auth) for @plugin_modules;
    $auth;
}

sub _normalize_login {
    my ($auth, $login) = @_;
    $login //= '';
    my $normalized_login = ($case_sensitive_login ? $login : lc $login);
    $normalized_login =~ s/^\s+//;
    $normalized_login =~ s/\s+$//;
    $normalized_login = $_->normalize_login($normalized_login) for @{$auth->{modules}};
    $normalized_login;
}

sub recheck_authentication_basic {
    my ($auth, $login, $passwd, $l7r) = @_;
    $auth->{login} eq $login and $auth->{passwd} eq $passwd;
}

sub authenticate_basic {
    my ($auth, $login, $passwd, $l7r) = @_;
    if (defined (my $normalized_login = $auth->_normalize_login($login))) {
        DEBUG "authenticating user $login ($normalized_login) with modules @{$auth->{modules}}";
        for (@{$auth->{modules}}) {
            if ($_->authenticate_basic($auth, $normalized_login, $passwd, $l7r)) {
                $auth->{login} = $login;
                $auth->{normalized_login} = $normalized_login;
                $auth->{passwd} = $passwd;
                $auth->{params}{'qvd.vm.user.name'} = $normalized_login;
                return 1;
            }
        }
    }
    else {
        ERROR "login normalization for '$login' failed";
    }
    return ();
}

sub normalized_login { shift->{normalized_login} // croak "internal error: user not authenticated yet!" }

sub login { shift->{login} // croak "internal error: user not authenticated yet!" }

sub params { %{shift->{params}} }

sub before_connect_to_vm {
    my $auth = shift;
    DEBUG "calling before_connect_to_vm hook";
    $_->before_connect_to_vm($auth) for @{$auth->{modules}};
}

sub before_list_of_vms {
    my $auth = shift;
    DEBUG "calling before_list_of_vms hook";
    $_->before_list_of_vms($auth) for @{$auth->{modules}};
}

sub allow_access_to_vm {
    my ($auth, $vm) = @_;
    DEBUG "calling allow_access_to_vm hook";
    for (@{$auth->{modules}}) {
        $_->allow_access_to_vm($auth, $vm) or return;
    }
    return 1;
}

1;
