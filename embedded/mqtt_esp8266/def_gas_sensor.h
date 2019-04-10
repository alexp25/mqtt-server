
#define WITH_SENSOR 1


int send_array_data[10];
char send_buf[100];

void init_sensor() {
  
}

int val = 0;

void read_sensor() {
   val = analogRead(A0);
//  val += 1;
//  if (val >= 1000) {
//    val = 0;
//  }
  send_array_data[0] =  val;
}
