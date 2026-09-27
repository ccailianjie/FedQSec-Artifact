simple NetCloud
{
    parameters:
        int numNodes = default(0);
        int numReplicas = default(4);
        int numRsu = default(2);
        double v2iDelay @unit(s) = default(10ms);
        double backhaulDelay @unit(s) = default(50ms);
        double cloudDelay @unit(s) = default(10ms);
    gates:
        input in[numNodes];
        output out[numNodes];
}
