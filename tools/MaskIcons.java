import java.awt.*;
import java.awt.geom.*;
import java.awt.image.*;
import java.io.*;
import javax.imageio.ImageIO;
public class MaskIcons {
 public static void main(String[] args) throws Exception {
  for(String filename:args){
   BufferedImage src=ImageIO.read(new File(filename));
   BufferedImage mask=new BufferedImage(src.getWidth(),src.getHeight(),BufferedImage.TYPE_INT_ARGB);
   Graphics2D g=mask.createGraphics();
   g.setRenderingHint(RenderingHints.KEY_ANTIALIASING,RenderingHints.VALUE_ANTIALIAS_ON);
   g.scale(src.getWidth()/100.0,src.getHeight()/100.0);
   Path2D p=new Path2D.Double();
   p.moveTo(0,42.7);p.curveTo(0,27.7,0,20.3,2.9,14.6);p.curveTo(5.5,9.5,9.5,5.5,14.6,2.9);p.curveTo(20.3,0,27.7,0,42.7,0);p.lineTo(57.3,0);
   p.curveTo(72.3,0,79.7,0,85.4,2.9);p.curveTo(90.5,5.5,94.5,9.5,97.1,14.6);p.curveTo(100,20.3,100,27.7,100,42.7);p.lineTo(100,57.3);
   p.curveTo(100,72.3,100,79.7,97.1,85.4);p.curveTo(94.5,90.5,90.5,94.5,85.4,97.1);p.curveTo(79.7,100,72.3,100,57.3,100);p.lineTo(42.7,100);
   p.curveTo(27.7,100,20.3,100,14.6,97.1);p.curveTo(9.5,94.5,5.5,90.5,2.9,85.4);p.curveTo(0,79.7,0,72.3,0,57.3);p.closePath();
   g.setColor(Color.WHITE);g.fill(p);g.dispose();
   BufferedImage out=new BufferedImage(src.getWidth(),src.getHeight(),BufferedImage.TYPE_INT_ARGB);
   g=out.createGraphics();g.setRenderingHint(RenderingHints.KEY_INTERPOLATION,RenderingHints.VALUE_INTERPOLATION_BICUBIC);int w=(int)Math.round(src.getWidth()*1.45),h=(int)Math.round(src.getHeight()*1.45);g.drawImage(src,(src.getWidth()-w)/2,(src.getHeight()-h)/2,w,h,null);g.setComposite(AlphaComposite.DstIn);g.drawImage(mask,0,0,null);g.dispose();
   ImageIO.write(out,"png",new File(filename.replace(".png",".masked.png")));
  }
 }
}
