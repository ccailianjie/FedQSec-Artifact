//
// PBFT consortium-blockchain simulation message.
//
cplusplus {{
#include "BcCommon.h"
}}

message BcMessage
{
    int type = 1;        // TX_REQUEST
    int senderId = -1;
    int destId = -1;
    int clientId = -1;   // originating vehicle id
    int txId = -1;       // transaction id (per client)
    string pid = "";
    int seq = -1;        // PBFT sequence number (assigned by primary)
    int view = 0;        // PBFT view number
    int txCategory = 0;  // CAT_CERT
    int creditScore = 100;
    int txCount = 0;     // number of transactions packed in this block (PRE-PREPARE)
    string digest = "";
    string payload = "";
    simtime_t txTs = 0;  // transaction creation time (for E2E latency)
}
