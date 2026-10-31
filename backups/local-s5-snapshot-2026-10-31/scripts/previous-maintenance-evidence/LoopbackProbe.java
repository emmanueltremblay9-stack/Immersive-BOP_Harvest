import java.nio.channels.Selector;
import java.net.InetAddress;
import java.net.ServerSocket;
public class LoopbackProbe {
    public static void main(String[] args) throws Exception {
        System.out.println("java.home=" + System.getProperty("java.home"));
        try (ServerSocket socket = new ServerSocket(0, 1, InetAddress.getLoopbackAddress())) {
            System.out.println("TCP loopback bind passed");
        }
        try (Selector selector = Selector.open()) {
            System.out.println("NIO selector open passed");
        }
    }
}
