network BlockchainNet
{
    parameters:
        int numReplicas = default(4);
        int numRsu = default(2);
        int numVehicles = default(12);
        double v2iDelay @unit(s) = default(10ms);
        double backhaulDelay @unit(s) = default(50ms);
        double cloudDelay @unit(s) = default(10ms);
        double verifyTime @unit(s) = default(0.97ms);
        double signTime @unit(s) = default(2.89ms);
        double blockInterval @unit(s) = default(1s);
        int maxTxPerBlock = default(1000);
        int blockHeaderSize = default(80);
        int eventRecordSize = default(74);
        int trustRecordSize = default(2009);
        double trustUpdateInterval @unit(s) = default(600s);
        double commitTime @unit(s) = default(10ms);
    submodules:
        cloud[numReplicas]: CloudReplica {
            parameters:
                id = index;
                numReplicas = parent.numReplicas;
                isPrimary = (index == 0);
                verifyTime = parent.verifyTime;
                blockInterval = parent.blockInterval;
                maxTxPerBlock = parent.maxTxPerBlock;
                blockHeaderSize = parent.blockHeaderSize;
                eventRecordSize = parent.eventRecordSize;
                trustRecordSize = parent.trustRecordSize;
                commitTime = parent.commitTime;
        }
        rsu[numRsu]: RsuNode {
            parameters:
                id = parent.numReplicas + index;
                numReplicas = parent.numReplicas;
                primaryId = 0;
                verifyTime = parent.verifyTime;
        }
        vehicle[numVehicles]: VehicleNode {
            parameters:
                id = parent.numReplicas + parent.numRsu + index;
                numReplicas = parent.numReplicas;
                numRsu = parent.numRsu;
                rsuBase = parent.numReplicas;
                signTime = parent.signTime;
                trustUpdateInterval = parent.trustUpdateInterval;
        }
        net: NetCloud {
            parameters:
                numNodes = parent.numReplicas + parent.numRsu + parent.numVehicles;
                numReplicas = parent.numReplicas;
                numRsu = parent.numRsu;
                v2iDelay = parent.v2iDelay;
                backhaulDelay = parent.backhaulDelay;
                cloudDelay = parent.cloudDelay;
        }
    connections:
        for i=0..numReplicas-1 {
            cloud[i].out --> net.in[i];
            net.out[i] --> cloud[i].in;
        }
        for i=0..numRsu-1 {
            rsu[i].out --> net.in[numReplicas+i];
            net.out[numReplicas+i] --> rsu[i].in;
        }
        for i=0..numVehicles-1 {
            vehicle[i].out --> net.in[numReplicas+numRsu+i];
            net.out[numReplicas+numRsu+i] --> vehicle[i].in;
        }
}
