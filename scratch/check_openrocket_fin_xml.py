import subprocess

code = """
import info.openrocket.core.rocketcomponent.FreeformFinSet;
import info.openrocket.core.file.openrocket.export.OpenRocketSaver;
import info.openrocket.core.document.OpenRocketDocument;
import info.openrocket.core.rocketcomponent.Rocket;
import info.openrocket.core.rocketcomponent.Stage;
import info.openrocket.core.rocketcomponent.BodyTube;
import info.openrocket.core.util.Coordinate;
import java.io.ByteArrayOutputStream;

public class TestFinClass {
    public static void main(String[] args) {
        try {
            Rocket r = new Rocket();
            Stage s = new Stage();
            r.addChild(s);
            BodyTube b = new BodyTube();
            s.addChild(b);
            FreeformFinSet fin = new FreeformFinSet();
            fin.setFinCount(4);
            fin.addPoint(new Coordinate(0, 0, 0));
            fin.addPoint(new Coordinate(0.04, 0.08, 0));
            fin.addPoint(new Coordinate(0.05, 0.08, 0));
            fin.addPoint(new Coordinate(0.05, 0, 0));
            b.addChild(fin);
            OpenRocketDocument doc = new OpenRocketDocument(r);
            OpenRocketSaver saver = new OpenRocketSaver();
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            saver.save(out, doc);
            System.out.println("SAVED XML:");
            System.out.println(new String(out.toByteArray(), "UTF-8"));
        } catch (Throwable t) {
            t.printStackTrace();
        }
    }
}
"""

with open('scratch/TestFinClass.java', 'w', encoding='utf-8') as f:
    f.write(code)

res = subprocess.run([
    'java', '-cp', 'C:\\Program Files\\OpenRocket\\jar\\OpenRocket-24.12.jar;scratch',
    'scratch/TestFinClass.java'
], capture_output=True, text=True)

print("STDOUT:")
print(res.stdout)
print("STDERR:")
print(res.stderr)
