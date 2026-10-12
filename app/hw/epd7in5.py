# *****************************************************************************
# * | File        :	  Pico_ePaper-7.5.py
# * | Author      :   Waveshare team
# * | Function    :   Electronic paper driver
# * | Info        :
# *----------------
# * | This version:   V1.0
# * | Date        :   2021-05-27
# # | Info        :   python demo
# -----------------------------------------------------------------------------
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documnetation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to  whom the Software is
# furished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS OR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

# [수정 2026-10] 원본 Pico_ePaper-7.5.py 에서 바뀐 점
#   - 생성자 인자 gray4(기본 False): 쓰지 않는 4계조 버퍼(96KB)를 만들지 않음
#   - 생성자 인자 baudrate(기본 10MHz, 원래 4MHz), set_baudrate(): SPI 속도 조절
#     (2026-10-10 실측: 10MHz에서 화면 정상, 전송 4771ms → 126ms)
#   - 빠른 전송: send_frame() / display_fast() / display_Partial_fast()
#     버퍼를 viper 함수로 한 번에 반전한 뒤 spi.write() 한 번으로 전송
#   - 원래 함수(display, display_Partial 등)는 그대로 남겨 둠 (비교용)

from machine import Pin, SPI
import framebuf
import micropython
import utime

# Display resolution
EPD_WIDTH       = 800
EPD_HEIGHT      = 480

RST_PIN         = 12
DC_PIN          = 8
CS_PIN          = 9
BUSY_PIN        = 13

@micropython.viper
def _invert(src: ptr8, dst: ptr8, n: int):
    # dst[i] = ~src[i]  (기계어로 컴파일되어 48KB 기준 수 ms)
    for i in range(n):
        dst[i] = src[i] ^ 0xFF


class EPD_7in5:
    def __init__(self, gray4=False, baudrate=10_000_000):
        self.reset_pin = Pin(RST_PIN, Pin.OUT)
        
        self.busy_pin = Pin(BUSY_PIN, Pin.IN, Pin.PULL_UP)
        self.cs_pin = Pin(CS_PIN, Pin.OUT)
        self.width = EPD_WIDTH
        self.height = EPD_HEIGHT
        
        self.black = 0x00
        self.white = 0xff
        self.darkgray = 0xaa
        self.grayish = 0x55

        self.spi = SPI(1)
        self.spi.init(baudrate=baudrate)
        # 주의: SPI(1)의 기본 MISO가 GP8(=DC)이라서 반드시 SPI 설정 *뒤에* DC 핀을 만든다
        self.dc_pin = Pin(DC_PIN, Pin.OUT)
        
        self.buffer_1Gray = bytearray(self.height * self.width // 8)
        self.buffer_inv = bytearray(self.height * self.width // 8)   # 반전 전송용
        self.image1Gray = framebuf.FrameBuffer(self.buffer_1Gray, self.width, self.height, framebuf.MONO_HLSB)
        if gray4:
            self.buffer_4Gray = bytearray(self.height * self.width // 4)
            self.image4Gray = framebuf.FrameBuffer(self.buffer_4Gray, self.width, self.height, framebuf.GS2_HMSB)
        else:
            self.buffer_4Gray = None
            self.image4Gray = None
        self.init()

    # ------------------------------------------------------------ 추가: SPI 속도
    def set_baudrate(self, baudrate):
        self.spi.init(baudrate=baudrate)
        self.dc_pin = Pin(DC_PIN, Pin.OUT)   # SPI 재설정 후 GP8을 다시 DC 출력으로
        return str(self.spi)

    # ------------------------------------------------------------ 추가: 빠른 전송
    def _write_buf(self, buf):
        self.dc_pin.value(1)
        self.cs_pin.value(0)
        self.spi.write(buf)
        self.cs_pin.value(1)

    def send_frame(self, Image):
        """화면 RAM에 한 프레임 전송만 함 (갱신은 하지 않음).
        원래 display()와 같은 데이터를 같은 순서로 보낸다:
        0x10 = 원본 그대로, 0x13 = 반전."""
        self.send_command(0x10)
        self._write_buf(Image)
        _invert(Image, self.buffer_inv, len(Image))
        self.send_command(0x13)
        self._write_buf(self.buffer_inv)

    def display_fast(self, Image):
        """display()와 결과는 같고 전송만 빠른 버전. full/fast 모드 모두 사용."""
        self.send_frame(Image)
        self.TurnOnDisplay()

    def display_partial_full(self, Image):
        """화면 전체를 부분 갱신 (깜빡임 없음, 약 0.4초). init_part() 다음에 부른다.
        deep sleep 을 거쳐도 비교 기준이 맞도록, 직전 화면(buffer_inv 에 남아 있음)을
        '이전 데이터'(0x10)로 먼저 보내고 새 화면을 0x13 으로 보낸다."""
        self.send_command(0x50)
        self.send_data(0xA9)
        self.send_data(0x07)
        self.send_command(0x91)              # partial in
        self.send_command(0x90)              # 창 = 화면 전체
        for v in (0, 0, (self.width - 1) >> 8, (self.width - 1) & 0xFF,
                  0, 0, (self.height - 1) >> 8, (self.height - 1) & 0xFF, 0x01):
            self.send_data(v)
        self.send_command(0x10)
        self._write_buf(self.buffer_inv)     # 직전 화면
        _invert(Image, self.buffer_inv, len(Image))
        self.send_command(0x13)
        self._write_buf(self.buffer_inv)     # 새 화면
        self.send_command(0x12)
        self.delay_ms(100)
        self.WaitUntilIdle()

    def send_frame_slow(self, Image):
        """원래 display()의 전송 부분만 (비교 측정용, 갱신 안 함)."""
        high = self.height
        wide = self.width // 8
        self.send_command(0x10)
        for i in range(0, wide):
            self.send_data1(Image[(i * high) : ((i+1) * high)])
        self.send_command(0x13)
        for j in range(high):
            for i in range(wide):
                self.send_data(~Image[i + j * wide])

    def display_Partial_fast(self, Image, Xstart, Ystart, Xend, Yend):
        """display_Partial()의 빠른 버전.
        Image = 영역 크기만 한 버퍼 ((Xend-Xstart)/8 * (Yend-Ystart) 바이트).
        Xstart, Xend 는 8의 배수여야 함."""
        if Xstart % 8 or Xend % 8:
            raise ValueError("Xstart/Xend must be multiples of 8")
        n = (Xend - Xstart) // 8 * (Yend - Ystart)
        if len(Image) < n:
            raise ValueError("Image buffer too small for region")

        self.send_command(0x50)
        self.send_data(0xA9)
        self.send_data(0x07)

        self.send_command(0x91)		#This command makes the display enter partial mode
        self.send_command(0x90)		#resolution setting
        self.send_data(Xstart//256)
        self.send_data(Xstart%256)
        self.send_data((Xend-1)//256)
        self.send_data((Xend-1)%256)
        self.send_data(Ystart//256)
        self.send_data(Ystart%256)
        self.send_data((Yend-1)//256)
        self.send_data((Yend-1)%256)
        self.send_data(0x01)

        _invert(Image, self.buffer_inv, n)
        self.send_command(0x13)
        self._write_buf(memoryview(self.buffer_inv)[:n])

        self.send_command(0x12)
        self.delay_ms(100)
        self.WaitUntilIdle()

    def digital_write(self, pin, value):
        pin.value(value)

    def digital_read(self, pin):
        return pin.value()

    def delay_ms(self, delaytime):
        utime.sleep(delaytime / 1000.0)

    def spi_writebyte(self, data):
        self.spi.write(bytearray(data))

    def module_exit(self):
        self.digital_write(self.reset_pin, 0)

    # Hardware reset
    def reset(self):
        self.digital_write(self.reset_pin, 1)
        self.delay_ms(50) 
        self.digital_write(self.reset_pin, 0)
        self.delay_ms(2)
        self.digital_write(self.reset_pin, 1)
        self.delay_ms(50)   

    def send_command(self, command):
        self.digital_write(self.dc_pin, 0)
        self.digital_write(self.cs_pin, 0)
        self.spi_writebyte([command])
        self.digital_write(self.cs_pin, 1)

    def send_data(self, data):
        self.digital_write(self.dc_pin, 1)
        self.digital_write(self.cs_pin, 0)
        self.spi_writebyte([data])
        self.digital_write(self.cs_pin, 1)
        
    def send_data1(self, buf):
        self.digital_write(self.dc_pin, 1)
        self.digital_write(self.cs_pin, 0)
        self.spi.write(bytearray(buf))
        self.digital_write(self.cs_pin, 1)

    def WaitUntilIdle(self):
        print("e-Paper busy")
        while(self.digital_read(self.busy_pin) == 0):    # Wait until the busy_pin goes LOW
            self.send_command(0x71)
            self.delay_ms(20)
        self.delay_ms(20) 
        print("e-Paper busy release")  

    def TurnOnDisplay(self):
        self.send_command(0x12) # DISPLAY REFRESH
        self.delay_ms(100)      #!!!The delay here is necessary, 200uS at least!!!
        self.WaitUntilIdle()
        
    def init(self):
        self.reset()
        
        self.send_command(0x06)     # btst
        self.send_data(0x17)
        self.send_data(0x17)
        self.send_data(0x28)        # If an exception is displayed, try using 0x38
        self.send_data(0x17)
        
        self.send_command(0x01)			#POWER SETTING
        self.send_data(0x07)
        self.send_data(0x07)    #VGH=20V,VGL=-20V
        self.send_data(0x28)		#VDH=15V
        self.send_data(0x17)		#VDL=-15V

        self.send_command(0x04) #POWER ON
        self.delay_ms(100)
        self.WaitUntilIdle()

        self.send_command(0X00)			#PANNEL SETTING
        self.send_data(0x1F)   #KW-3f   KWR-2F	BWROTP 0f	BWOTP 1f

        self.send_command(0x61)        	#tres
        self.send_data(0x03)		#source 800
        self.send_data(0x20)
        self.send_data(0x01)		#gate 480
        self.send_data(0xE0)

        self.send_command(0X15)
        self.send_data(0x00)

        # If the screen appears gray, use the annotated initialization command
        self.send_command(0X50)
        self.send_data(0x10)
        self.send_data(0x07)
        # self.send_command(0X50)
        # self.send_data(0x10)
        # self.send_data(0x17)
        # self.send_command(0X52)		
        # self.send_data(0x03)


        self.send_command(0X60)			#TCON SETTING
        self.send_data(0x22)

        # EPD hardware init end
        return 0
    
    def init_fast(self):
        self.reset()
        
        self.send_command(0X00)			#PANNEL SETTING
        self.send_data(0x1F)   #KW-3f   KWR-2F	BWROTP 0f	BWOTP 1f

        # If the screen appears gray, use the annotated initialization command
        self.send_command(0X50)
        self.send_data(0x10)
        self.send_data(0x07)
        # self.send_command(0X50)
        # self.send_data(0x10)
        # self.send_data(0x17)
        # self.send_command(0X52)		
        # self.send_data(0x03)


        self.send_command(0x04) #POWER ON
        self.delay_ms(100) 
        self.WaitUntilIdle()        #waiting for the electronic paper IC to release the idle signal

        #Enhanced display drive(Add 0x06 command)
        self.send_command(0x06)			#Booster Soft Start 
        self.send_data (0x27)
        self.send_data (0x27)   
        self.send_data (0x18)		
        self.send_data (0x17)		

        self.send_command(0xE0)
        self.send_data(0x02)
        self.send_command(0xE5)
        self.send_data(0x5A)

        # EPD hardware init end
        return 0
    
    def init_part(self):
        self.reset()

        self.send_command(0X00)			#PANNEL SETTING
        self.send_data(0x1F)   #KW-3f   KWR-2F	BWROTP 0f	BWOTP 1f

        self.send_command(0x04) #POWER ON
        self.delay_ms(100) 
        self.WaitUntilIdle()        #waiting for the electronic paper IC to release the idle signal

        self.send_command(0xE0)
        self.send_data(0x02)
        self.send_command(0xE5)
        self.send_data(0x6E)

        # EPD hardware init end
        return 0
    
    # The feature will only be available on screens sold after 24/10/23
    def init_4Gray(self):
        # EPD hardware init start
        self.reset()

        self.send_command(0X00)			#PANNEL SETTING
        self.send_data(0x1F)   #KW-3f   KWR-2F	BWROTP 0f	BWOTP 1f
        
        self.send_command(0X50)
        self.send_data(0x10)
        self.send_data(0x07)

        self.send_command(0x04) #POWER ON
        self.delay_ms(100) 
        self.WaitUntilIdle()        #waiting for the electronic paper IC to release the idle signal

        #Enhanced display drive(Add 0x06 command)
        self.send_command(0x06)			#Booster Soft Start 
        self.send_data (0x27)
        self.send_data (0x27)   
        self.send_data (0x18)		
        self.send_data (0x17)	

        self.send_command(0xE0)
        self.send_data(0x02)
        self.send_command(0xE5)
        self.send_data(0x5F)

        # EPD hardware init end
        return 0

    def Clear(self):
        
        high = self.height
        if( self.width % 8 == 0) :
            wide =  self.width // 8
        else :
            wide =  self.width // 8 + 1
        
        self.send_command(0x10)
        for i in range(0, wide):
            self.send_data1([0xff] * high)
                
        self.send_command(0x13) 
        for i in range(0, wide):
            self.send_data1([0x00] * high)
                
        self.TurnOnDisplay()
        
    def ClearBlack(self):
        
        high = self.height
        if( self.width % 8 == 0) :
            wide =  self.width // 8
        else :
            wide =  self.width // 8 + 1
        
        self.send_command(0x10)
        for i in range(0, wide):
            self.send_data1([0x00] * high)
                
        self.send_command(0x13) 
        for i in range(0, wide):
            self.send_data1([0xff] * high)
                
        self.TurnOnDisplay()
        
    def display(self,Image):
        high = self.height
        if( self.width % 8 == 0) :
            wide =  self.width // 8
        else :
            wide =  self.width // 8 + 1
                       
        self.send_command(0x10) 
        for i in range(0, wide):
            self.send_data1(Image[(i * high) : ((i+1) * high)])
        
        self.send_command(0x13) 
        for j in range(high):
            for i in range(wide):
                self.send_data(~Image[i + j * wide])
                
        self.TurnOnDisplay()
        
    def display_Partial(self, Image, Xstart, Ystart, Xend, Yend):
        if((Xstart % 8 + Xend % 8 == 8 & Xstart % 8 > Xend % 8) | Xstart % 8 + Xend % 8 == 0 | (Xend - Xstart)%8 == 0):
            Xstart = Xstart // 8 * 8
            Xend = Xend // 8 * 8
        else:
            Xstart = Xstart // 8 * 8
            if Xend % 8 == 0:
                Xend = Xend // 8 * 8
            else:
                Xend = Xend // 8 * 8 + 1
                
        Width = (Xend - Xstart) // 8
        Height = Yend - Ystart
	
        self.send_command(0x50)
        self.send_data(0xA9)
        self.send_data(0x07)

        self.send_command(0x91)		#This command makes the display enter partial mode
        self.send_command(0x90)		#resolution setting
        self.send_data(Xstart//256)
        self.send_data(Xstart%256)   #x-start    

        self.send_data((Xend-1)//256)		
        self.send_data((Xend-1)%256)  #x-end	

        self.send_data(Ystart//256)  #
        self.send_data(Ystart%256)   #y-start    

        self.send_data((Yend-1)//256)		
        self.send_data((Yend-1)%256)  #y-end
        self.send_data(0x01)
                       
        self.send_command(0x13) 
        for j in range(Height):
            for i in range(Width):
                self.send_data(~Image[i + j * Width])
        

        self.send_command(0x12)
        self.delay_ms(100)
        self.WaitUntilIdle()

    def display_4Gray(self, image):
        self.send_command(0x10)
        for i in range(0, 48000):     
            temp3=0
            for j in range(0, 2):
                temp1 = image[i*2+j]
                for k in range(0, 2):
                    temp2 = temp1&0x03 
                    if(temp2 == 0x03):
                        temp3 |= 0x01   # white
                    elif(temp2 == 0x00):
                        temp3 |= 0x00   # black
                    elif(temp2 == 0x02):
                        temp3 |= 0x01   # gray1
                    else:   # 0x01
                        temp3 |= 0x00   # gray2
                    temp3 <<= 1

                    temp1 >>= 2
                    temp2 = temp1&0x03 
                    if(temp2 == 0x03):   # white
                        temp3 |= 0x01
                    elif(temp2 == 0x00):   # black
                        temp3 |= 0x00
                    elif(temp2 == 0x02):
                        temp3 |= 0x01   # gray1
                    else:   # 0x01
                        temp3 |= 0x00   # gray2
                    
                    if (( j!=1 ) | ( k!=1 )):
                        temp3 <<= 1

                    temp1 >>= 2
            self.send_data(temp3)
            
        self.send_command(0x13)	       
        for i in range(0, 48000):       
            temp3=0
            for j in range(0, 2):
                temp1 = image[i*2+j]
                for k in range(0, 2):
                    temp2 = temp1&0x03 
                    if(temp2 == 0x03):
                        temp3 |= 0x01   # white
                    elif(temp2 == 0x00):
                        temp3 |= 0x00   # black
                    elif(temp2 == 0x02):
                        temp3 |= 0x00   # gray1
                    else:   # 0x01
                        temp3 |= 0x01   # gray2
                    temp3 <<= 1

                    temp1 >>= 2
                    temp2 = temp1&0x03
                    if(temp2 == 0x03):   # white
                        temp3 |= 0x01
                    elif(temp2 == 0x00):   # black
                        temp3 |= 0x00
                    elif(temp2 == 0x02):
                        temp3 |= 0x00   # gray1
                    else:   # 0x01
                        temp3 |= 0x01   # gray2
                    
                    if (( j!=1 ) | ( k!=1 )):
                        temp3 <<= 1

                    temp1 >>= 2
            self.send_data(temp3)
        
        self.send_command(0x12)
        self.delay_ms(100)
        self.WaitUntilIdle()


    def sleep(self):
        self.send_command(0x50)
        self.send_data(0XF7)
        self.send_command(0x02) # power off
        self.WaitUntilIdle()
        self.send_command(0x07) # deep sleep
        self.send_data(0xa5)

if __name__=='__main__':
    epd = EPD_7in5(gray4=True)
    epd.Clear()
    
    epd.image1Gray.fill(0xFF)
    
    epd.image1Gray.text("Waveshare", 5, 10, 0x00)
    epd.image1Gray.text("Pico_ePaper-7.5", 5, 40, 0x00)
    epd.image1Gray.text("Raspberry Pico", 5, 70, 0x00)
    epd.display(epd.buffer_1Gray)
    epd.delay_ms(5000)
    
    epd.image1Gray.vline(10, 90, 60, 0x00)
    epd.image1Gray.vline(120, 90, 60, 0x00)
    epd.image1Gray.hline(10, 90, 110, 0x00)
    epd.image1Gray.hline(10, 150, 110, 0x00)
    epd.image1Gray.line(10, 90, 120, 150, 0x00)
    epd.image1Gray.line(120, 90, 10, 150, 0x00)
    epd.display(epd.buffer_1Gray)
    epd.delay_ms(5000)
    
    epd.image1Gray.rect(10, 180, 50, 80, 0x00)
    epd.image1Gray.fill_rect(70, 180, 50, 80, 0x00)
    epd.display(epd.buffer_1Gray)
    epd.delay_ms(5000)
    
    epd.image1Gray.fill_rect(250, 150, 480, 20, 0x00)
    epd.image1Gray.fill_rect(250, 310, 480, 20, 0x00)
    epd.image1Gray.fill_rect(400, 0, 20, 480, 0x00)
    epd.image1Gray.fill_rect(560, 0, 20, 480, 0x00)

    for j in range(0, 3):
        for i in range(0, 15):
            epd.image1Gray.line(270+j*160+i, 20+j*160, 375+j*160+i, 140+j*160, 0x00)
        for i in range(0, 15):
            epd.image1Gray.line(375+j*160+i, 20+j*160, 270+j*160+i, 140+j*160, 0x00)
        for i in range(0, 15):
            epd.image1Gray.line(270+j*160, 20+j*160+i, 390+j*160, 125+j*160+i, 0x00)
        for i in range(0, 15):
            epd.image1Gray.line(270+j*160, 125+j*160+i, 390+j*160, 20+j*160+i, 0x00)        
    epd.image1Gray.fill_rect(270, 190, 100, 100, 0x00)
    epd.image1Gray.fill_rect(270, 350, 100, 100, 0x00)
    epd.display(epd.buffer_1Gray)
    epd.delay_ms(5000)
    
    # epd.init_part()
    # for i in range(0, 10):
    #     epd.image1Gray.fill_rect(40, 260, 40, 10, 0x00)
    #     epd.image1Gray.text(str(i), 60, 260, 0xFF)
    #     epd.display_Partial(epd.buffer_1Gray, 0, 0, 800, 480)

    # # The feature will only be available on screens sold after 24/10/23
    # print("Four grayscale refresh")
    # epd.init_4Gray()
    # epd.image4Gray.fill_rect(150, 10, 250, 30, epd.black)
    # epd.image4Gray.text('GRAY1 with black background',155, 21, epd.white)
    # epd.image4Gray.text('GRAY2 with white background',155, 51, epd.grayish)
    # epd.image4Gray.text('GRAY3 with white background',155, 81, epd.darkgray)
    # epd.image4Gray.text('GRAY4 with white background',155, 111, epd.black)
    # epd.display_4Gray(epd.buffer_4Gray)
    # epd.delay_ms(5000)
     
    epd.init() 
    epd.Clear()
    epd.delay_ms(2000)
    print("sleep")
    epd.sleep()
