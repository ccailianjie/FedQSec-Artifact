simple CloudReplica
{
    parameters:
        int id = default(0);
        int numReplicas = default(4);
        bool isPrimary = default(false);
        double verifyTime @unit(s) = default(0.97ms);
        int maxTxPerBlock = default(1000);
        int blockHeaderSize = default(80);
        int eventRecordSize = default(74);   // PID32 + Acc32 + Timestamp8 + VerResult1 + EventType1
        int trustRecordSize = default(2009);   // Trust Record：PID32+PK1300+C2+Ts8+Type1+Sig666 = 2009 B
        double commitTime @unit(s) = default(10ms);
        double blockInterval @unit(s) = default(1s);
        bool centralized = default(false);
    gates:
        input in;
        output out;
}
