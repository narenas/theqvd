package QVD::VMKiller::LXC;

use strict;
use warnings;
use 5.010;

use Fcntl qw(LOCK_EX LOCK_NB);

BEGIN { $QVD::Config::USE_DB = 0 }
use QVD::Config;
use QVD::Log;

sub kill_dangling_vms {

    my $path_cgroup = cfg('path.cgroup');
    my $lock_file = cfg('internal.hkd.lock.path');

    open my $lock, '>', $lock_file or
       ERROR("Unable to open lock file $lock_file: $^E"),
       return;
    if (flock $lock, LOCK_EX|LOCK_NB) {
        for my $dir (<$path_cgroup/qvd-*>) {
            my ($container) = $dir =~ m|/(qvd-[^/]*$)|;
            DEBUG "reading LXC $container process IDs";
            if (open my $fh, '<', "$dir/cgroup.procs") {
                chomp (my @pids = <$fh>);
                if (@pids) {
                    INFO sprintf("killing %d processes from container %s", scalar(@pids), ($1 // '<unknown>'));
                    kill KILL => @pids;
                }
                else {
                    DEBUG "LXC $container has no processes";
                }
            }
        }
    }
    else {
        DEBUG "HKD is running";
    }
}

1;

# FIXME, reword this description

__END__

=head1 TITLE

qvd-killer-lxc - The orphaned QVD containers killer.

=head1 DESCRIPTION

Kill any QVD container that keeps still running after
the controlling HKD daemon has terminated.

This program is intended to be run for cron every minute. If the HKD
is running it will exit immediately. Otherwise it will look for QVD
containers that may still be running and kill all its processes.

Under normal operation, the HKD will stop any container and its
processes before exiting. If for whatever reason that doesn't happen
(for instance, due to some software bug or the HKD process being
killed) any orphaned containers must be killed in order to avoid any
possibility of having it running simultaneously in two QVD nodes, as
eventually, another node from the QVD cluster will detect the failed
HKD and reclaim the containers it was managing that then, could be
started in another node.



=cut

