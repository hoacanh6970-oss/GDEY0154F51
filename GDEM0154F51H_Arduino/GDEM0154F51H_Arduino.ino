#include <SPI.h>
//EPD
#include "Display_EPD_W21_spi.h"
#include "Display_EPD_W21.h"
#include "Ap_29demo.h"  

void setup() {
#ifdef ESP8266
   pinMode(D0, INPUT);  //BUSY
   pinMode(D1, OUTPUT); //RES 
   pinMode(D2, OUTPUT); //DC   
   pinMode(D4, OUTPUT); //CS     
#endif 
#ifdef Arduino_UNO
   pinMode(4, INPUT);  //BUSY
   pinMode(5, OUTPUT); //RES 
   pinMode(6, OUTPUT); //DC   
   pinMode(7, OUTPUT); //CS   
#endif 
   //SPI
   SPI.beginTransaction(SPISettings(10000000, MSBFIRST, SPI_MODE0)); 
   SPI.begin ();  
}


//Tips//
/*
1.Flickering is normal when EPD is performing a full screen update to clear ghosting from the previous image so to ensure better clarity and legibility for the new image.
2.There will be no flicker when EPD performs a partial upadte.
3.Please make sue that EPD enters sleep mode when upadte is completed and always leave the sleep mode command. Otherwise, this may result in a reduced lifespan of EPD.
4.Please refrain from inserting EPD to the FPC socket or unplugging it when the MCU is being powered to prevent potential damage.)
5.Re-initialization is required for every full screen update.
6.When porting the program, set the BUSY pin to input mode and other pins to output mode.
*/
void loop() {
#if 1//Full screen upadte demostration.
  /************Full display*******************/
    EPD_init(); //Full screen update initialization.
    PIC_display(gImage_1);//To Display one image using full screen update.
    EPD_sleep();//Enter the sleep mode and please do not delete it, otherwise it will reduce the lifespan of the screen.
    delay(3000); //Delay for 3s.
 	/************Fast update mode(12s)*******************/
	#if 1 //Fast update demostration.	
		EPD_init_Fast(); //Fast screen update initialization.
		PIC_display(gImage_1);//To Display one image using full screen update.
		EPD_sleep();//Enter the sleep mode and please do not delete it, otherwise it will reduce the lifespan of the screen.
    delay(3000); //Delay for 3s.
  #endif	  
  #if 0//Demonstration of Display 4 colors, to enable this feature, please change 0 to 1.
   /************Full display*******************/
    EPD_init(); //Full screen upadte initialization.
    Display_All_Black();//To Display one image using full screen upadte.
    EPD_sleep();//Enter the sleep mode and please do not delete it, otherwise it will reduce the lifespan of the screen.
    delay(3000); //Delay for 3s.
    
    EPD_init(); //Full screen upadte initialization.
    Display_All_Yellow();//To Display one image using full screen upadte.
    EPD_sleep();//Enter the sleep mode and please do not delete it, otherwise it will reduce the lifespan of the screen.
    delay(3000); //Delay for 3s.

    EPD_init(); //Full screen upadte initialization.
    Display_All_Red();//To Display one image using full screen upadte.
    EPD_sleep();//Enter the sleep mode and please do not delete it, otherwise it will reduce the lifespan of the screen.
    delay(3000); //Delay for 3s.  
  #endif    
    EPD_init(); //Full screen upadte initialization.
    Display_All_White(); //Clear screen function.
    EPD_sleep();//Enter the sleep mode and please do not delete it, otherwise it will reduce the lifespan of the screen.. 
        
#endif   
#ifdef ESP8266
  while(1) 
    {
     Sys_run();//System run
     LED_run();//Breathing lamp
    }
#endif
#ifdef Arduino_UNO
 while(1);  // The program stops here   
#endif
}




//////////////////////////////////END//////////////////////////////////////////////////
