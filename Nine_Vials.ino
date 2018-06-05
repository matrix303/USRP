#include <OneWire.h>
#include <DallasTemperature.h>

//default settings
int OD_SET[9] = {0, 0, 0, 0, 0, 0, 0, 0, 0}; //default signal set for each vial
float SET_POINT[9] = {37.0,37.0,37.0,37.0,37.0,37.0,37.0,37.0,37.0}; //default temperature for each vial

//Defining pins for each vial module
int MOT_I[9]    = { 26, 11,  6, 14, 19, 42, 52,A14, 47}; //motor to pump fluid in
int MOT_O[9]    = { 34, 24, 10,  5, 15, 50, A3, 49, 39}; //motor to pump fluid out
int MOT_STIR[9] = { 30, 13,  8,  3, 17, 46, A1, 53, 43}; //stirring fan
int PELTIER[9]  = { 32, 22,  9,  4, 16, 48, A2, 51, 41}; //heating tile
int LED[9]      = { 28, 12,  7,  2, 18, 44, A0, A15, 45}; //LED that shines through vial
int SENSOR[9]   = { A4, A5, A6, A7, A8, A9, A10, A11, A12}; //light sensor to measure turbidity
int Thermometer[9]   = {38,36,25,27,29,37,35,33,31};
int OD[9]; //array to hold light sensor values

//Defining pins and target for temperature control
int ONE_WIRE_BUS = 23; // onewire for temperature sensor data
float VIAL_TEMP[9]; //will hold the temperature data for each vial
int numberOfDevices; //number of temerature sensors detected
int mode = 0; // 0 is standby, 1 is experiement, and 2 is manual
int new_mode = 0; // flag which indicates a mode change, will break out of any loops
bool mode_change = 0; // flag to indicate that the mode has been changed 
bool setup_flag = 0; // flag which indicates whether or not the setup has been done
DeviceAddress TEMP_ADDRESS[9]; //array will be filled with temperature sensor addresses out of order
//array of temperature sensor addresses, will be filled in the correct order
DeviceAddress TEMP_SENSOR[9] = {{0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00}, 
                                 {0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00},
                                 {0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00},
                                 {0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00},
                                 {0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00},
                                 {0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00},
                                 {0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00},
                                 {0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00},
                                 {0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00}};

OneWire oneWire(ONE_WIRE_BUS); //set up oneWire instance
DallasTemperature sensors(&oneWire); //pass this to Dallas library

///////////////////////////////////////////////////////////      Main Program Start      ///////////////////////////////////////////////////////////

// system setup start
void setup() {
  Serial.begin(9600);
  module_setup(); //assigning pins with output mode to module components
  thermometer_setup(); //determines how many temperature sensors are present and which vial each one corresponds to
  print_info(); // prints number of devices, followed by all device addresses
  temp_control_setup(); //warmup tiles and then start capturing readings from temperature sensors
}
int n=0;///////
void loop() {  //~900s

  if(mode_change){
    for (int i=0;i<9;i++){
      digitalWrite(LED[i],HIGH);
      digitalWrite(MOT_STIR[i],LOW);
      digitalWrite(MOT_I[i],LOW);
      digitalWrite(MOT_O[i],LOW);
      digitalWrite(PELTIER[i], LOW);
    }
    mode = new_mode;
    mode_change = 0;
  }
  
  while (mode == 0){
    updater();
    if (mode_change){
      break;
    }     
    delay(1000);
  }

  while (mode == 1){ // experiment mode
    measure_LED(); // turn LED on and off and measure light intensity       // 20*N s
    if (mode_change){
      break;
    }
    check_temperatures();
    if (mode_change){
      break;
    }
    set_peltier();                                                          //  6s
    if (mode_change){
      break;
    }
    stir(4);  // N = 2s
    if (mode_change){
      break;
    }

    // if (n==8){//////////pump in once/8 cycle
    //   pump_in(1); // prevent depletion
    //   n=0;
    // }//////
    // else{
    //   n=n+1;
    // }
  
    for(int i=0;i<3;i++){                                            // 16*3 = 48s 
      turbido_pump_in(2); // motors pump nutrients in to maintian OD (for tudbidostat)
      if (mode_change){
        break;
      }
      stir(4);
      if (mode_change){
        break;
      }
      delay(2000);//2s
      pump_out(8); // motors pump fluid out (for tudbidostat)
      if (mode_change){
        break;
      }
      pump_off();//make sure that the pump is off
      if (mode_change){
        break;
      }
    }
    if (mode_change){
      break;
    }
    measure_LED();                                                            //20s
    if (mode_change){
      break;
    }
    check_temperatures();
    if (mode_change){
      break;
    }
    set_peltier();
    if (mode_change){
      break;
    }      
                                                                                        //=80s  
    for (int l=0; l<4; l++){                                                   //210*4 = 840s
      pump_out(5);
      if (mode_change){
        break;
      }
      for (int l=0; l<10; l++){                                                 //20.5*10= 205
        stir(int(float(19)-float(numberOfDevices)*1.25));                         //19 s  stir18~5.5
        if (mode_change){
          break;
        }
        delay(1000);                                                              //1s
        check_temperatures();                                                      //N*0.25
        if (mode_change){
          break;
        }
        delay(50);    
        set_peltier(); // adjust heating tiles based on vial temperatures ,   //takes N seconds with N vials
        if (mode_change){
          break;
        }
        delay(50);
      }
    }
    if (mode_change){
      break;
    }
  }
  
  while (mode == 2){ // pump mode
    for (int i=0;i<9;i++){
      if(check_address(TEMP_SENSOR[i])){
        digitalWrite(LED[i],LOW);
        digitalWrite(MOT_STIR[i],HIGH);
        digitalWrite(MOT_I[i],HIGH);
        digitalWrite(MOT_O[i],HIGH);
        delay(3000);
        digitalWrite(MOT_I[i],LOW);
        delay(6000);
        digitalWrite(MOT_O[i],LOW);
        Serial.println(OD[i]);
        updater();
      }
    }
  }
  
  if ((mode == 3)&&(setup_flag == 0)){ // setup mode
    setup_flag = 1;
    module_setup(); //assigning pins with output mode to module components
    thermometer_setup(); //determines how many temperature sensors are present and which vial each one corresponds to
    print_info(); // prints number of devices, followed by all device addresses
    temp_control_setup();  
  }
}

///////////////////////////////////////////////////////////   Main Program End   ///////////////////////////////////////////////////////////

///////////////////////////////////////////////////////////      Functions      ///////////////////////////////////////////////////////////

// reads data from serial port
void updater(){
  if (Serial.available() == 46) {
    char input_byte[46];
    for(int i = 0; i < 46; i++){
      input_byte[i] = Serial.read();
    }
    while (Serial.available()) { // flush incoming serial port
      Serial.read();
    }
    // Serial.print("received");
    new_mode = int(input_byte[0] - '0');
    if (new_mode != mode){
      mode_change = 1;
      return;
    }
    for (int i = 0; i <9; i ++){
      SET_POINT[i] = int(input_byte[i*5+1] - '0')*10 + int(input_byte[i*5+2] - '0');
      OD_SET[i] = int(input_byte[i*5+3] - '0')*100 + int(input_byte[i*5+4] - '0')*10 + int(input_byte[i*5+5] - '0');
    }
  }
  if (OD_full() && mode == 1){ //print data as soon as OD data starts to come in
    print_data();
  }
  if (mode == 0){
    Serial.print(127); // signals python to send data
    Serial.print(" ");
    Serial.print(0);
    Serial.print(" ");
    Serial.println(0);
  }
}

//Sets all module pins to output
void module_setup(){
  for (int i=0; i<9; i++){
    pinMode(MOT_I[i], OUTPUT);
    pinMode(MOT_O[i],OUTPUT);
    pinMode(MOT_STIR[i], OUTPUT);
    pinMode(PELTIER[i],OUTPUT);
    delay(500);
    pinMode(Thermometer[i],OUTPUT);
    pinMode(LED[i],OUTPUT);   
    for (int j=0; j<9; j++){
      digitalWrite(LED[i], LOW);
      delay(250);
      digitalWrite(LED[i], HIGH);
      digitalWrite(PELTIER[i], HIGH);
      delay(250);
      digitalWrite(PELTIER[i], LOW);
      digitalWrite(LED[i], LOW);
    }
  } 
}

//Determine numberOfDevices and which vial corresponds to which temperature sensor
void thermometer_setup(){ 
  sensors.begin();  // Start up the library
  for (int k = 0; k < 9; k++){
    digitalWrite(Thermometer[k], LOW);//turn on all the Thermometer
  }
  // locate devices on the bus
  numberOfDevices = sensors.getDeviceCount();
  // Serial.println(numberOfDevices);
  // assign addresses to TEMP_ADDRESS array (in no particular order)
  for(int i = 0; i < numberOfDevices; i++){
    oneWire.search(TEMP_ADDRESS[i]);
    delay(100);
  }
  for (int k = 0; k < 9; k++){
    digitalWrite(Thermometer[k], HIGH);//turn off all the sensors
    //delay(1000);
  }
  //turn each temperature sensors on and off to decide corresponded address
  for (int k = 0; k < 9; k++){
    digitalWrite(Thermometer[k], LOW);//turn ON the sensor
    delay(1000);
    for (int i = 0; i < numberOfDevices; i++){
      if (sensors.readPowerSupply(TEMP_ADDRESS[i])==0){
        for(int j = 0; j < 8; j++){
          TEMP_SENSOR[k][j] = TEMP_ADDRESS[i][j];    
        }
        //digitalWrite(MOT_STIR[portorder[k]], LOW);
        digitalWrite(LED[k], HIGH);
        delay(100);
        digitalWrite(MOT_STIR[k], HIGH);
        delay(100);
      }
    }
   digitalWrite(Thermometer[k], HIGH);//turn off the Thermometer
   //delay(1000);
  }
  for (int k = 0; k < 9; k++){ //turn ON all the tempsensors for exp usefrom time import sleep
    digitalWrite(Thermometer[k], LOW);
  }
  int numbersofsensors=0;
  // show the addresses we found on the bus
  for (int i = 0; i < 9; i++){
    if (check_address(TEMP_SENSOR[i])) {
      sensors.setResolution(TEMP_SENSOR[i], 12); //sets resolution of temperature sensor data to 12 bit
      numbersofsensors=numbersofsensors+1;
    }
  }
  if (numbersofsensors!= numberOfDevices){
    delay(1000);
    for (int i = 0; i < 9; i++){
      digitalWrite(MOT_STIR[i], LOW);
    }
    delay(1000);
    module_setup();
    thermometer_setup();
  }
}

void print_info(){
  Serial.print(numberOfDevices);
  for (int i = 0; i < 9; i++){
    if (check_address(TEMP_SENSOR[i])){
      Serial.print(" ");
      printAddress(TEMP_SENSOR[i]); // print sensor address
    }
    else {
      Serial.print(" 0000000000000000"); // no sensor
    }
  }
  Serial.println();
}

//returns true if address is full and false if address is empty
bool check_address(DeviceAddress address){
  for (int i = 0; i < 8; i++){
    if (address[i] != 0x00){
      return (true);
    }
  }
  return (false);
}

//set up temperature control system (peltiers)
void temp_control_setup(){
  for (int i = 0; i<9; i++){
    if(check_address(TEMP_SENSOR[i])){
      digitalWrite(PELTIER[i],HIGH);
      delay(1000);
    }
  }
}

//checks if OD data has started coming in
bool OD_full(){
  for (int i = 0; i < 9; i++){
    if (OD[i] != 0){
      return (true);
    }
  }
  return (false);
}

void turbido_pump_in(int time) {
  for (int i=0; i<9; i++){
    if(check_address(TEMP_SENSOR[i])&&(OD[i] < OD_SET[i])){
      digitalWrite(PELTIER[i],HIGH);
      digitalWrite(MOT_I[i], HIGH);
      updater();
      if (mode_change){
        return;
      }
    }
  }
  for (int i = 0; i <time; i++){
    updater();
    if (mode_change){
      return;
    }
    delay(1000);
  }  
  for (int i=0; i<9; i++){
    if(check_address(TEMP_SENSOR[i])){
      digitalWrite(MOT_I[i], LOW);
      updater();
      if (mode_change){
        return;
      }
    }
  }
}

void pump_in(int time) {
  for (int i=0; i<9; i++){
    digitalWrite(PELTIER[i],HIGH);
    digitalWrite(MOT_I[i], HIGH);
    updater();
    if (mode_change){
      return;
    }
  }
  for (int i = 0; i <time; i++){
    updater();
    if (mode_change){
      return;
    }
    delay(1000);
  }
  for (int i=0; i<9; i++){
    if(check_address(TEMP_SENSOR[i])){
      digitalWrite(MOT_I[i], LOW);
      updater();
      if (mode_change){
        return;
      }
    }
  }
}

void pump_out(int time) {
  for (int i=0; i<9; i++){
    //if(check_address(TEMP_SENSOR[i])&&(OD[i] < OD_SET[i])){
    if(check_address(TEMP_SENSOR[i])){//always turn on pump out
      digitalWrite(MOT_O[i], HIGH);
      updater();
      if (mode_change){
        return;
      }
      delay(25);
    }
  }
  for (int i = 0; i <time; i++){
    updater();
    if (mode_change){
      return;
    }
    delay(1000);
  }
  for (int i=0; i<9; i++){
    if(check_address(TEMP_SENSOR[i])){
      digitalWrite(MOT_O[i], LOW);
      updater();
      if (mode_change){
        return;
      }
      delay(25);
    }
  }
}

// turn off the pumps
void pump_off() {
  for (int i=0; i<9; i++){
    digitalWrite(MOT_I[i], LOW);
    delay(25);
    updater();
    if (mode_change){
      return;
    }
    digitalWrite(MOT_O[i], LOW);
    delay(25);
    updater();
    if (mode_change){
      return;
    }
  }
}
  
// activates the stirring fans
void stir(int time) {
  for (int i=0; i<9; i++){
    if(check_address(TEMP_SENSOR[i])){
      digitalWrite(MOT_STIR[i], HIGH);
      updater();
      if (mode_change){
        return;
      }
      delay(25);
    }
  }
  for (int i = 0; i <time; i++){
    updater();
    if (mode_change){
      return;
    }
    delay(1000);
  }
  for (int i=0; i<9; i++){
    if(check_address(TEMP_SENSOR[i])){
      digitalWrite(MOT_STIR[i], LOW);
      updater();
      if (mode_change){
        return;
      }
      delay(25);
    }
  }
}

// requests vial temperatures and saves them into VIAL_TEMP
void check_temperatures(){
  sensors.requestTemperatures(); // Send the command to get temperatures
  for(int i = 0; i<9; i++){
    if(check_address(TEMP_SENSOR[i])){
      VIAL_TEMP[i] = sensors.getTempC(TEMP_SENSOR[i]);
      delay(25);
    }
  }
  updater();
}

// sets each peltier either on or off depending on VIAL_TEMP
void set_peltier() { // N seconds
  for (int i=0; i<9; i++){
    if(check_address(TEMP_SENSOR[i])){
      if (VIAL_TEMP[i] < SET_POINT[i]){
        digitalWrite(PELTIER[i],HIGH);
        updater();
        if (mode_change){
          return;
        }
        delay(1000);  
      }
      else{
      digitalWrite(PELTIER[i],LOW);
      updater();
      if (mode_change){
        return;
      }
      delay(1000);  
      }
    }
  }
}

// reads signal from light sensor
void OD_signal_read (int s) {
  float ODsen = 0;
  int NumOfPoints = 3;
  for (int j=0; j < NumOfPoints; j++){
    stir(1);
    delay(1000);
    ODsen= ODsen + analogRead(SENSOR[s]);
  }
  OD[s] = int(float(ODsen)/float(NumOfPoints));
}

// controls LED and light sensor
void measure_LED(){                                           //20s
  for (int i = 0; i < 9; i++){
    digitalWrite(PELTIER[i],LOW);
    updater();
    if (mode_change){
      return;
    }
  }
  stir(2);                                               //2s
  for (int i = 0; i < 9; i++){                 //4*N =   16s
    if(check_address(TEMP_SENSOR[i])){
      delay(50);
      digitalWrite(LED[i], LOW);
      updater();
      if (mode_change){
        return;
      }
      delay(1000);                             //1s
      OD_signal_read(i);/////////////////        20s
      updater();
      if (mode_change){
        return;
      }
      delay(50);
      digitalWrite(LED[i], HIGH);
      updater();
      if (mode_change){
        return;
      }
    }
  }
}

//prints out the data for each vial
void print_data(){
  for (int i =0; i<9; i++){
    if(check_address(TEMP_SENSOR[i])){
      Serial.print(OD[i]);
      Serial.print(" ");
      Serial.print(OD_SET[i]);
      Serial.print(" ");
      Serial.print(VIAL_TEMP[i]);
      Serial.print(" ");
      Serial.print(SET_POINT[i]);
      Serial.print(" ");
      Serial.print(abs(digitalRead(LED[i])-1));//bc LED controlled as inverse
      Serial.print(" ");
      Serial.print(digitalRead(PELTIER[i]));
      Serial.print(" ");
      Serial.print(digitalRead(MOT_STIR[i]));
      Serial.print(" ");
      Serial.print(digitalRead(MOT_I[i]));
      Serial.print(" ");
      Serial.print(digitalRead(MOT_O[i]));
      Serial.print(" ");
    }
    else {
      Serial.print(0);
      Serial.print(" ");
      Serial.print(0);
      Serial.print(" ");
      Serial.print(0);
      Serial.print(" ");
      Serial.print(0);
      Serial.print(" ");
      Serial.print(0);
      Serial.print(" ");
      Serial.print(0);
      Serial.print(" ");
      Serial.print(0);
      Serial.print(" ");
      Serial.print(0);
      Serial.print(" ");
      Serial.print(0);
      Serial.print(" ");
    }
  }
  Serial.println();
}

// function to print a device address
void printAddress(DeviceAddress deviceAddress){
  for (uint8_t i = 0; i < 8; i++){
    if (deviceAddress[i] < 16){
      Serial.print("0"); // zero pad the address if necessary
    }
    Serial.print(deviceAddress[i], HEX);
  }
}

