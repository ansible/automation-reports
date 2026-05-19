import * as React from 'react';
import {
  Alert,
  Button,
  Label,
  Spinner,
  Toolbar,
  ToolbarContent,
  ToolbarItem,
} from '@patternfly/react-core';
import { LockIcon, SyncAltIcon } from '@patternfly/react-icons';
import useClusterStore from '@app/Store/clusterStore';
import { ClusterInfo } from '@app/Types/ClusterTypes';

interface ClusterListProps {
  onAddCluster: () => void;
}

function formatLastSynced(value: string | null): string {
  if (!value) {
    return 'Never';
  }
  try {
    const date = new Date(value);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    const diffDays = Math.floor(diffHours / 24);
    if (diffDays < 30) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  } catch {
    return value;
  }
}

const ClusterRow: React.FC<{ cluster: ClusterInfo }> = ({ cluster }) => {
  const syncCluster = useClusterStore((s) => s.syncCluster);
  const deleteCluster = useClusterStore((s) => s.deleteCluster);
  const startEdit = useClusterStore((s) => s.startEdit);
  const syncing = useClusterStore((s) => s.syncing);
  const isSyncing = syncing.includes(cluster.id);

  const [confirmDelete, setConfirmDelete] = React.useState(false);
  const [deleteError, setDeleteError] = React.useState<string | null>(null);

  const address = `${cluster.protocol}://${cluster.address}:${cluster.port}`;

  const handleDelete = async () => {
    if (!confirmDelete) {
      setConfirmDelete(true);
      return;
    }
    try {
      await deleteCluster(cluster.id);
    } catch {
      setDeleteError('Failed to delete cluster');
      setConfirmDelete(false);
    }
  };

  const handleSync = async () => {
    await syncCluster(cluster.id);
  };

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        padding: '12px 0',
        borderBottom: '1px solid var(--pf-v6-global--BorderColor--100)',
        flexWrap: 'wrap',
      }}
    >
      <div style={{ flex: '1 1 220px', minWidth: 0 }}>
        <span style={{ fontWeight: 500, wordBreak: 'break-all' }}>{address}</span>
      </div>

      <div style={{ flex: '0 0 auto' }}>
        <Label color="blue" isCompact>
          {cluster.aap_version}
        </Label>
      </div>

      <div style={{ flex: '0 0 auto' }}>
        {cluster.verify_ssl ? (
          <Label color="green" icon={<LockIcon />} isCompact>
            SSL verified
          </Label>
        ) : (
          <Label color="orange" isCompact>
            SSL unverified
          </Label>
        )}
      </div>

      <div style={{ flex: '0 0 120px', color: 'var(--pf-v6-global--Color--200)', fontSize: '0.875rem' }}>
        {formatLastSynced(cluster.last_synced)}
      </div>

      <div style={{ flex: '0 0 auto', display: 'flex', gap: '8px', alignItems: 'center' }}>
        <Button variant="secondary" size="sm" onClick={() => startEdit(cluster)}>
          Edit
        </Button>
        <Button
          variant="secondary"
          size="sm"
          onClick={handleSync}
          isDisabled={isSyncing}
          icon={isSyncing ? <Spinner size="sm" /> : <SyncAltIcon />}
        >
          {isSyncing ? 'Syncing…' : 'Sync Now'}
        </Button>
        {confirmDelete ? (
          <>
            <Button variant="danger" size="sm" onClick={handleDelete}>
              Confirm Delete
            </Button>
            <Button variant="link" size="sm" onClick={() => setConfirmDelete(false)}>
              Cancel
            </Button>
          </>
        ) : (
          <Button variant="danger" size="sm" onClick={handleDelete}>
            Delete
          </Button>
        )}
      </div>

      {deleteError && (
        <div style={{ width: '100%' }}>
          <Alert variant="danger" isInline isPlain title={deleteError} />
        </div>
      )}
    </div>
  );
};

export const ClusterList: React.FC<ClusterListProps> = ({ onAddCluster }) => {
  const clusters = useClusterStore((s) => s.clusters);
  const error = useClusterStore((s) => s.error);

  return (
    <div>
      <Toolbar>
        <ToolbarContent>
          <ToolbarItem align={{ default: 'alignEnd' }}>
            <Button variant="primary" onClick={onAddCluster}>
              Add Cluster
            </Button>
          </ToolbarItem>
        </ToolbarContent>
      </Toolbar>

      {error && <Alert variant="danger" isInline title={error} style={{ marginBottom: '16px' }} />}

      {clusters.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '32px', color: 'var(--pf-v6-global--Color--200)' }}>
          No clusters configured. Click &quot;Add Cluster&quot; to get started.
        </div>
      ) : (
        <div>
          {clusters.map((cluster) => (
            <ClusterRow key={cluster.id} cluster={cluster} />
          ))}
        </div>
      )}
    </div>
  );
};

export default ClusterList;
