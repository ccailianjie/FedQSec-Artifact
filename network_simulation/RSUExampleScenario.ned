import org.car2x.veins.nodes.RSU;
import org.car2x.veins.nodes.Scenario;

network RSUExampleScenario extends Scenario
{
    @display();
    submodules:
        rsu[5]: RSU {
        }
}
