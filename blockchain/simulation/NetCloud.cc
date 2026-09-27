#include <omnetpp.h>
#include "BcMessage_m.h"
#include "BcCommon.h"

using namespace omnetpp;

// Wide-area IoV network relay: three link classes with distinct delays.
//   v2iDelay      : vehicle <-> RSU (DSRC / C-V2X PC5, short range)
//   backhaulDelay : RSU <-> cloud, vehicle <-> cloud (cellular backhaul / WAN)
//   cloudDelay    : cloud validator <-> cloud validator (datacenter / WAN)
class NetCloud : public cSimpleModule
{
  protected:
    simtime_t v2iDelay;
    simtime_t backhaulDelay;
    simtime_t cloudDelay;
    int numReplicas;
    int numRsu;
    long relayed = 0;

    virtual void initialize() override {
        v2iDelay = par("v2iDelay");
        backhaulDelay = par("backhaulDelay");
        cloudDelay = par("cloudDelay");
        numReplicas = par("numReplicas");
        numRsu = par("numRsu");
    }
    virtual void handleMessage(cMessage *msg) override {
        BcMessage *bc = check_and_cast<BcMessage*>(msg);
        int src = msg->getArrivalGate()->getIndex();
        int dst = bc->getDestId();
        if (dst < 0 || dst >= gateSize("out")) {
            EV_WARN << "NetCloud: invalid destId=" << dst << " from " << src << ", dropping\n";
            delete bc;
            return;
        }
        int rsuBase = numReplicas;
        int vehBase = numReplicas + numRsu;
        bool srcCloud = src < numReplicas;
        bool dstCloud = dst < numReplicas;
        bool srcRsu = src >= rsuBase && src < vehBase;
        bool dstRsu = dst >= rsuBase && dst < vehBase;
        bool srcVeh = src >= vehBase;
        bool dstVeh = dst >= vehBase;

        simtime_t d;
        if (srcCloud && dstCloud) d = cloudDelay;                        // validator <-> validator
        else if ((srcVeh && dstRsu) || (srcRsu && dstVeh)) d = v2iDelay; // V2I short range
        else d = backhaulDelay;                                          // RSU<->cloud / vehicle<->cloud

        relayed++;
        sendDelayed(bc, d, "out", dst);
    }
    virtual void finish() override {
        recordScalar("relayedMessages", relayed);
    }
};

Define_Module(NetCloud);
