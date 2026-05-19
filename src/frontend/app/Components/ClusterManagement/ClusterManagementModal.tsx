import * as React from 'react';
import { Modal, ModalBody, ModalHeader, Spinner } from '@patternfly/react-core';
import useClusterStore from '@app/Store/clusterStore';
import { ClusterList } from './ClusterList';
import { ClusterForm } from './ClusterForm';

export const ClusterManagementModal: React.FC = () => {
  const isModalOpen = useClusterStore((s) => s.isModalOpen);
  const formMode = useClusterStore((s) => s.formMode);
  const editingCluster = useClusterStore((s) => s.editingCluster);
  const clusters = useClusterStore((s) => s.clusters);
  const loading = useClusterStore((s) => s.loading);
  const closeModal = useClusterStore((s) => s.closeModal);
  const startAdd = useClusterStore((s) => s.startAdd);
  const saveCluster = useClusterStore((s) => s.saveCluster);
  const backToList = useClusterStore((s) => s.backToList);

  const title =
    formMode === 'list'
      ? 'Cluster Management'
      : formMode === 'add'
        ? 'Add Cluster'
        : 'Edit Cluster';

  return (
    <Modal
      isOpen={isModalOpen}
      onClose={closeModal}
      variant="large"
      aria-label="Cluster management"
    >
      <ModalHeader title={title} />
      <ModalBody>
        {loading && clusters.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '32px' }}>
            <Spinner aria-label="Loading clusters" />
          </div>
        ) : formMode === 'list' ? (
          <ClusterList onAddCluster={() => startAdd()} />
        ) : formMode === 'add' ? (
          <ClusterForm
            mode="add"
            onSave={saveCluster}
            onCancel={backToList}
          />
        ) : (
          <ClusterForm
            mode="edit"
            cluster={editingCluster ?? undefined}
            onSave={saveCluster}
            onCancel={backToList}
          />
        )}
      </ModalBody>
    </Modal>
  );
};

export default ClusterManagementModal;
