# OVN DB Backup and Recovery

## OVN Database Startup Validation and Single-Member Recovery

During startup in Raft mode, `ovn-central` and OVN-IC databases validate database identity, storage format and clustered log state. If validation fails, the original database and Raft header are preserved and the process exits nonzero.

| Database state | Startup behavior |
| --- | --- |
| Valid clustered database | Start normally and let Raft synchronize the member. |
| Valid standalone database | Preserve the existing standalone startup path. |
| Missing database | Preserve the existing initialization and header recovery paths. |
| Pending cluster join | Resume the join and keep the existing stale pending-join cleanup. |
| Unknown identity, unexpected name, unknown format or invalid clustered log | Preserve the original file and header. Rebuild only when a valid matching Raft header and reachable quorum are available; otherwise remain blocked for retry. |

Do not run `ovsdb-tool fix-cluster` followed by `join-cluster` on an existing invalid member. A local repair can discard committed log entries that are missing locally. The startup path requires a valid Raft header, verifies it against a reachable majority, and creates a `rejoin-cluster` database with the original server ID and peer addresses. Only after the new file is created successfully is the original database moved to a timestamped backup. The healthy majority then repopulates the clean member through normal Raft log or snapshot synchronization.

If the disk is still full, the header is invalid, the quorum is unavailable or replacement fails, startup exits nonzero and leaves the original file untouched. Clustered database readiness and liveness checks also run `ovsdb-tool check-cluster`; a semantic persistence gap therefore removes the member from service and lets kubelet restart it. A process or Pod reporting Ready alone does not prove that the database history is safe.

Automatic recovery is limited to one damaged member at a time. It does not reconcile multiple divergent members. Before explicit recovery, preserve each member's database, header, backups and logs; compare cluster/server identities, snapshot and log history, terms, committed entries and application data; and reconcile conflicting histories explicitly. File sizes and commit indexes alone do not identify an authoritative copy.

This startup protection does not repair already divergent histories or the underlying I/O failure. It limits automatic recovery to a fresh member that can synchronize from a reachable, consistent majority. See [Issue #7870](https://github.com/kubeovn/kube-ovn/issues/7870).

This document describes how to perform database backups and how to
perform cluster recovery from existing database files in different situations.

## Database Backup

The database files can be backed up for recovery in case of failure. Use
the backup command of the kubectl plugin:

```bash
# kubectl ko nb backup
tar: Removing leading `/' from member names
backup ovn-nb db to /root/ovnnb_db.060223191654183154.backup

# kubectl ko sb backup
tar: Removing leading `/' from member names
backup ovn-nb db to /root/ovnsb_db.060223191654183154.backup
```

## Cluster Partial Nodes Failure Recovery

If some nodes in the cluster are working abnormally due to power failure,
file system failure or lack of disk space, but the cluster is still working normally, you can recover it by following the steps below.

### Check the Logs to Confirm Status

Check the log in `/var/log/ovn/ovn-northd.log`, if it shows similar error as follows,
you can make sure that there is an exception in the database:

```bash
 * ovn-northd is not running
ovsdb-server: ovsdb error: error reading record 2739 from OVN_Northbound log: record 2739 advances commit index to 6308 but last log index is 6307
 * Starting ovsdb-nb
```

### Kick Node from Cluster

Select the corresponding database for the operation based on whether the log prompt is `OVN_Northbound` or `OVN_Southbound`.
The above log prompt is `OVN_Northbound` then for ovn-nb do the following:

```bash
# kubectl ko nb status
9182
Name: OVN_Northbound
Cluster ID: e75f (e75fa340-49ed-45ab-990e-26cb865ebc85)
Server ID: 9182 (9182e8dd-b5b0-4dd8-8518-598cc1e374f3)
Address: tcp:[10.0.128.61]:6643
Status: cluster member
Role: leader
Term: 1454
Leader: self
Vote: self

Last Election started 1732603 ms ago, reason: timeout
Last Election won: 1732587 ms ago
Election timer: 1000
Log: [7332, 12512]
Entries not yet committed: 1
Entries not yet applied: 1
Connections: ->f080 <-f080 <-e631 ->e631
Disconnections: 1
Servers:
    f080 (f080 at tcp:[10.0.129.139]:6643) next_index=12512 match_index=12510 last msg 63 ms ago
    9182 (9182 at tcp:[10.0.128.61]:6643) (self) next_index=10394 match_index=12510
    e631 (e631 at tcp:[10.0.131.173]:6643) next_index=12512 match_index=0
```

Kick abnormal nodes from the cluster:

```bash
kubectl ko nb kick e631
```

Log in to the abnormal node and delete the database file:

```bash
mv /etc/origin/ovn/ovnnb_db.db /tmp
```

Delete the `ovn-central` pod of the corresponding node and wait for the cluster to recover:

```bash
kubectl delete pod -n kube-system ovn-central-xxxx
```

## Recover when Total Cluster Failed

If the majority of the cluster nodes are broken and the leader cannot be elected, please refer to the following steps to recover.

### Stop ovn-central

Record the current replicas of `ovn-central` and stop `ovn-central` to avoid new database changes that affect recovery:

```bash
kubectl scale deployment -n kube-system ovn-central --replicas=0
```

### Select a Backup

As most of the nodes are damaged, the cluster needs to be rebuilt by recovering from one of the database files.
If you have previously backed up the database you can use the previous backup file to restore it.
If not you can use the following steps to generate a backup from an existing file.

> Since the database file in the default folder is a cluster format database file containing information about
> the current cluster, you can't rebuild the database directly with this file,
> you need to use `ovsdb-tool cluster-to-standalone` to convert the format.

Select the first node in the `ovn-central` environment variable `NODE_IPS` to restore the database files.
If the database file of the first node is corrupted, copy the file from the other machine `/etc/origin/ovn` to
the first machine. Run the following command to generate a database file backup.

If `docker` is still available on the node:

```bash
docker run -it -v /etc/origin/ovn:/etc/ovn kubeovn/kube-ovn:{{ variables.version }} bash
cd /etc/ovn/
ovsdb-tool cluster-to-standalone ovnnb_db_standalone.db ovnnb_db.db
ovsdb-tool cluster-to-standalone ovnsb_db_standalone.db ovnsb_db.db
```

If the node uses containerd (without docker), you can pull and run the image directly via `ctr`:

```bash
ctr -n k8s.io image pull docker.io/kubeovn/kube-ovn:{{ variables.version }}
ctr -n k8s.io run --rm -t \
  --mount type=bind,src=/etc/origin/ovn,dst=/etc/ovn,options=rbind:rw \
  docker.io/kubeovn/kube-ovn:{{ variables.version }} ovn-recover bash
cd /etc/ovn/
ovsdb-tool cluster-to-standalone ovnnb_db_standalone.db ovnnb_db.db
ovsdb-tool cluster-to-standalone ovnsb_db_standalone.db ovnsb_db.db
exit
```

Alternatively, you can run `ovsdb-tool cluster-to-standalone` directly inside the `ovn-central` Pod, and then use `kubectl cp` to copy the backup files out.

### Delete the Database Files on All ovn-central Nodes

In order to avoid rebuilding the cluster with the wrong data, the existing database files need to be cleaned up:

```bash
mv /etc/origin/ovn/ovnnb_db.db /tmp
mv /etc/origin/ovn/ovnsb_db.db /tmp
```

### Recovering Database Cluster

Rename the backup databases to `ovnnb_db.db` and `ovnsb_db.db` respectively,
and copy them to the `/etc/origin/ovn/` directory of the first machine in the `ovn-central` environment variable `NODE_IPS`:

```bash
mv /etc/origin/ovn/ovnnb_db_standalone.db /etc/origin/ovn/ovnnb_db.db
mv /etc/origin/ovn/ovnsb_db_standalone.db /etc/origin/ovn/ovnsb_db.db
```

Restore the number of replicas of `ovn-central`:

```bash
kubectl scale deployment -n kube-system ovn-central --replicas=3
kubectl rollout status deployment/ovn-central -n kube-system
```
