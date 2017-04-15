#include <Audio.h>
#include <Wire.h>
#include <SPI.h>
#include <SD.h>
#include <SerialFlash.h>


const int FlashChipSelect = 6; 
/*// GUItool: begin automatically generated code
AudioPlaySerialflashRaw  playFlashRaw1;  //xy=374,181
AudioOutputI2S           i2s1;           //xy=641,129
AudioConnection          patchCord1(playFlashRaw1, 0, i2s1, 0);
AudioConnection          patchCord2(playFlashRaw1, 0, i2s1, 1);
AudioControlSGTL5000     sgtl5000_1;     //xy=477,271
// GUItool: end automatically generated code*/

// GUItool: begin automatically generated code
AudioPlaySerialflashRaw  playFlashRaw4;  //xy=270,57
AudioPlaySerialflashRaw  playFlashRaw2; //xy=275,141
AudioPlaySerialflashRaw  playFlashRaw3;  //xy=277,98
AudioPlaySerialflashRaw  playFlashRaw1;  //xy=283,179
AudioMixer4              mixer1;         //xy=535,72
AudioOutputI2S           i2s1;           //xy=641,129
AudioConnection          patchCord1(playFlashRaw4, 0, mixer1, 0);
AudioConnection          patchCord2(playFlashRaw2, 0, mixer1, 2);
AudioConnection          patchCord3(playFlashRaw3, 0, mixer1, 1);
AudioConnection          patchCord4(playFlashRaw1, 0, mixer1, 3);
AudioConnection          patchCord5(mixer1, 0, i2s1, 0);
AudioConnection          patchCord6(mixer1, 0, i2s1, 1);
AudioControlSGTL5000     sgtl5000_1;     //xy=477,271
// GUItool: end automatically generated code


#define N_SEQ 8 //defines number of sub-sequences or rows we have (# of rows)
#define N_BEATS 16 //defines the number of total beats in each sub-sequence (# of columns)

byte sequence[N_SEQ][N_BEATS]; //total sequence is an N_SEQ by N_BEATS array

float tempo = 180.; //manually set tempo - TODO read tempo from analog knob or other input (MIDI?)
unsigned long beat_duration_ms; 
elapsedMillis beat_timer_ms;
byte beat_number = 0; 

unsigned long compute_beat_duration_ms(float tempo) {
  // convert tempo (bpm) to beat time in milliseconds
  unsigned long beat_time_in_millis = 60000. / tempo / 4; //dimensional analysis: 60(s/min) * 1000(ms/s) / tempo(bpm) = 60,000(ms/min)/tempo(bpm)=millis per beat
  return beat_time_in_millis;
}

void erase_sequence() { //this function called in set up to clear all 
  for (byte seq=0; seq<N_SEQ; seq++) { //cycles through all the sub-sequences/rows to erase them all individually
    erase_sequence(seq);
  }
}

void erase_sequence(byte seq) { //erases a single sub-sequence/row
  for (byte beat=0; beat<N_BEATS; beat++) { //cycles through all the beats in the subsequence to erase them all
    sequence[seq][beat] = 0;
  }
}


bool check_for_new_sequence() {
  if (Serial.available()) {
    byte seq = Serial.read();
    if (seq > 7) {
      Serial.println("Error, invalid sequence");
      return false;
    }
    for (byte beat=0; beat<N_BEATS; beat++) {
      byte newVal = Serial.read();
      sequence[seq][beat]=newVal;
      Serial.print("new value ");
      Serial.println(newVal);
    }
    return true;
  }
  return false;
}



#include <Adafruit_NeoPixel.h>
#ifdef __AVR__
  #include <avr/power.h>
#endif

#define PIN            1

// How many NeoPixels are attached to the Arduino?
#define NUMPIXELS      144
Adafruit_NeoPixel pixels = Adafruit_NeoPixel(NUMPIXELS, PIN, NEO_GRB + NEO_KHZ800);

int k=0;

/*void update_metronome(byte beat_number) { 
  //update metronome to display beat_number (from 0 to 15)
  for(k=0; k<N_BEATS; k++){
    Serial.println(k);
    if (k!=beat_number){
      pixels.setPixelColor(k, pixels.Color(0,0,0));
    }
    else{
      pixels.setPixelColor(k, pixels.Color(0,80,0)); // Moderately bright green color.
    }
  }
  pixels.show(); // This sends the updated pixel color to the hardware.
}*/ //commented out right now b/c trying to test turning on two at a time - this is the normal one that turns on one per beat

/*void update_metronome(byte beat_number) { 
  //update metronome to display beat_number (from 0 to 15)
  for(k=0; k<N_BEATS*2; k++){
    Serial.println(k);
    if (k==beat_number*2){
      pixels.setPixelColor(k, pixels.Color(0,80,0)); // Moderately bright green color.
    }
    else if (k==beat_number*2+1){
      pixels.setPixelColor(k, pixels.Color(0,80,0)); // Moderately bright green color.
    }
    else{
      pixels.setPixelColor(k, pixels.Color(0,0,0));
    }
  }
  pixels.show(); // This sends the updated pixel color to the hardware.
}*/ //commented out because this is two at a time, trying for nine at a time below

void update_metronome(byte beat_number) { //updates the metronome nine at a time
  //update metronome to display beat_number (from 0 to 15)
  for(k=0; k<N_BEATS*9; k++){
    Serial.println(k);
    if (k>=beat_number*9 and k<(beat_number+1)*9){ //this is the key change from before, if statement defines the range over all nine consecutive led's
      pixels.setPixelColor(k, pixels.Color(0,80,0)); // Moderately bright green color.
    }
    else{
      pixels.setPixelColor(k, pixels.Color(0,0,0));
    }
  }
  pixels.show(); // This sends the updated pixel color to the hardware.
}

int sensorPin = A2;

void set_tempo(int sensorValue) {
  tempo = sensorValue/7.+40.; //takes the sensor value (an integer 1-1023) which is read off the analog pot, divids by 7 and adds to forty to set as the new tempo (in bpm) 
}


void update_display() {
  for(byte seq=0; seq<N_SEQ; seq++) {
    for (byte beat=0; beat<N_BEATS; beat++) {
      int led_index=seq*N_BEATS+beat+N_BEATS;
      switch (sequence[seq][beat]){
        case 0:
          pixels.setPixelColor(led_index, pixels.Color(0,0,0));
          break;
        case 1:
          pixels.setPixelColor(led_index, pixels.Color(0,0,80));
          break;
        case 2:
          pixels.setPixelColor(led_index, pixels.Color(80,0,0));
          break;
        case 3:
          pixels.setPixelColor(led_index, pixels.Color(35,35,35));
          break;
        default:
          pixels.setPixelColor(led_index, pixels.Color(0,80,0));
          break;
        
      }
      /*if (sequence[seq][beat] ==1) {
        pixels.setPixelColor(led_index, pixels.Color(0,150,0));
      }
      if (sequence[seq][beat]==2) {
        
      }
      else{
        pixels.setPixelColor(led_index, pixels.Color(0,0,0));
      }*/
    }
  }
  pixels.show();  
}

void play_sound(byte sound) {
  // play the raw file corresponding to this sound
  switch (sound) { //defines all the different cases
    /*case 0:
      // play sound 0
      Serial.println("playing sound 0");
      Serial.println(playFlashRaw1.play("0.RAW"));
      break;*/
    case 1:
      // play sound 01
      Serial.println("playing sound 01");
      Serial.println(playFlashRaw1.play("01.RAW"));
      delay(10);
      break; //it turns out that 01.RAW is the same sound as 0.RAW, so having both is redundant
    case 2:
      // play sound 2
      Serial.println("playing sound 2");
      Serial.println(playFlashRaw2.play("1.RAW"));
      break;
    case 3:
      // play sound 3
      Serial.println("playing sound 3");
      Serial.println(playFlashRaw3.play("2.RAW"));
      break;
    case 4:
      // play sound 4
      Serial.println("playing sound 4");
      Serial.println(playFlashRaw4.play("3.RAW"));
      break;
    case 5:
      // play sound 5
      Serial.println("playing sound 5");
      Serial.println(playFlashRaw1.play("4.RAW"));
      break;
    case 6:
      // play sound 6
      Serial.println("playing sound 6");
      Serial.println(playFlashRaw1.play("5.RAW"));
      break;
    case 7:
      // play sound 6
      Serial.println("playing sound 6");
      Serial.println(playFlashRaw1.play("6.RAW"));
      break;
    case 8:
      // play sound 7
      Serial.println("playing sound 7");
      Serial.println(playFlashRaw1.play("7.RAW"));
      break;
    case 9:
      // play sound 8.0
      Serial.println("playing sound 8.0");
      Serial.println(playFlashRaw1.play("80.RAW"));
      break;
    case 10:
      // play sound 8.1
      Serial.println("playing sound 8.1");
      Serial.println(playFlashRaw1.play("81.RAW"));
      break;
    case 11:
      // play sound 8.2
      Serial.println("playing sound 8.2");
      Serial.println(playFlashRaw1.play("82.RAW"));
      break;
    case 12:
      // play sound 8.3
      Serial.println("playing sound 8.3");
      Serial.println(playFlashRaw1.play("83.RAW"));
      break;
    default:
      Serial.println("unknown sound");
      break;
  }
}

void update_sounds(byte beat_number) {
  //play sounds for each sequence for this beat number
  for(byte seq=0; seq<N_SEQ; seq++) {
    if (sequence[seq][beat_number] !=0) {
      play_sound(sequence[seq][beat_number]);
      //TO DO how to handle playing multiple of same sound on same beat - probably want to just play that sound once
    }
  }
}

byte sound = 1;

void error(const char *message) {
  while (1) {
    Serial.println(message);
    delay(2500);
  }
}

void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);
  AudioMemory(8);
  sgtl5000_1.enable();
  sgtl5000_1.volume(0.5);
  SPI.setMOSI(7);
  SPI.setSCK(14);
  if (!SerialFlash.begin(FlashChipSelect)) {
    error("Unable to access SPI Flash chip");
  }
  /*beat_duration_ms = compute_beat_duration_ms(tempo);
  Serial.print("beat_duration_ms");
  Serial.println(beat_duration_ms);*/
  erase_sequence();
  //below is the sequence that we're just manually setting for now
  /*sequence[0][0] = 1;
  sequence[0][1] = 1;
  sequence[0][2] = 1;
  sequence[0][3] = 1;
  sequence[0][4] = 1;
  sequence[0][5] = 1;
  sequence[0][6] = 1;
  sequence[0][7] = 1;
  sequence[0][8] = 1;*/
  /*sequence[0][5] = 1;
  sequence[1][5] = 3;
  sequence[6][2] = 3;
  sequence[4][2] = 2;
  /*sequence[0][12] = 3;
  sequence[0][15] = 13;*/
  mixer1.gain(0,1.0);
  mixer1.gain(1,1.0);
  mixer1.gain(2,1.0);
  mixer1.gain(3,1.0);

  pixels.begin();
  update_display();
}

void loop() {
  // put your main code here, to run repeatedly:
  bool new_sequence = check_for_new_sequence();
  //update buttons
  //update display, if new sequence or buttons
  //march through sequence
  /*delay(1000);
  Serial.println("playing");
  playFlashRaw1.play("1.RAW");*/
  /*int sensorValue = analogRead(sensorPin);
  /*Serial.println(sensorValue);*/
  /*set_tempo(sensorValue);*/

  beat_duration_ms = compute_beat_duration_ms(tempo);
  /*Serial.print("beat_duration_ms");
  Serial.println(beat_duration_ms);*/
  if (beat_timer_ms > beat_duration_ms) { //cycles through the beat_numbers
    update_sounds(beat_number); //plays the sounds of the corresponding beat_number
    beat_timer_ms = 0;
    Serial.print("beat_number");
    Serial.println(beat_number);
    beat_number += 1;
    if (beat_number >= N_BEATS) beat_number=0;
  }
}
