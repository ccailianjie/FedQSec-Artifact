#pragma once
#include <omnetpp.h>
using namespace omnetpp;

// ---- PBFT message types ----
enum BcMsgType {
    TX_REQUEST  = 1,   // vehicle -> RSU (client transaction)
    TX_FORWARD  = 2,   // RSU -> primary replica
    PRE_PREPARE = 3,   // primary -> all replicas
    PREPARE     = 4,   // replica -> all replicas
    COMMIT      = 5,   // replica -> all replicas
    REPLY       = 6,   // replica -> client (vehicle)
    PREPARE_VERIFIED = 7,  // internal: quorum PREPARE signatures verified -> broadcast COMMIT
    COMMIT_VERIFIED  = 8   // internal: quorum COMMIT signatures verified -> execute
};

// ---- business transaction categories (consortium chain) ----
enum TxCategory {
    CAT_CERT       = 0,  // certificate / pseudonym management
    CAT_EVIDENCE   = 1,  // message evidence (tamper-proof log)
    CAT_TRUST_MGMT = 2,
    CAT_FEDLOG     = 3,  // federated-learning related logs
    CAT_TRUST      = 4
};

// global id layout: replicas [0, nR), RSUs [nR, nR+nRsu), vehicles [nR+nRsu, ...)
inline int rsuBaseId(int numReplicas)             { return numReplicas; }
inline int vehBaseId(int numReplicas, int numRsu) { return numReplicas + numRsu; }
inline int pbftF(int numReplicas)                 { return (numReplicas - 1) / 3; }
inline int prepareQuorum(int numReplicas)         { return 2 * pbftF(numReplicas) + 1; }
inline int replyQuorum(int numReplicas)           { return pbftF(numReplicas) + 1; }
