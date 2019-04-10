class SerialParser {
#define N_SERIAL_DATA_STR 40
#define N_SERIAL_DATA_VAL 20
    uint16_t data = 0;
    char inData[N_SERIAL_DATA_STR];
    char inData2[N_SERIAL_DATA_STR];
    int dataArray[N_SERIAL_DATA_VAL];
    char serialSendBuffer[100];
    uint8_t incomplete_line = 0;
    uint8_t index_serial_data = 0;

    int parseCSV(char* inputString, int *outputArray, int outputArraySize) {
      char *pch;
      int val = 0;
      int index_serial_data = 0;
      pch = strtok(inputString, ",");

      while (pch != NULL && pch != "\n") {
        //        sscanf (pch, "%d", &val);
        val = String(pch).toInt();
        outputArray[index_serial_data] = val;
        index_serial_data++;
        if (index_serial_data == outputArraySize) {
          break;
        }
        pch = strtok(NULL, ",");
      }
      return index_serial_data;
    }

  public:
    void check_com_raw(void (*onreceive) (char*)) {
      if (Serial.available() > 0)
      {
        char aChar = Serial.read();
        this->inData[index_serial_data] = aChar;
        this->index_serial_data++;
        if (aChar == '\n' || this->index_serial_data == N_SERIAL_DATA_STR - 1)
        {
          /**
             if previously there was an incomplete line
             ignore the line AND the next line (until the next \n)
          */
          uint8_t read_line = 1;
          if (this->incomplete_line) {
            this->incomplete_line = 0;
            read_line = 0;
          }
          if (aChar != '\n') {
            this->incomplete_line = 1;
            read_line = 0;
          }
          this->inData[this->index_serial_data] = '\0';

          if (read_line) {
            (*onreceive) (this->inData);
          }
          else
          {

          }

          this->inData[index_serial_data] = '\0'; // Keep the string NULL terminated
          this->index_serial_data = 0;
          this->inData[0] = '\0';
        }
      }
    }

    void check_com(void (*onparse)(int, int*)) {
      if (Serial.available() > 0)
      {
        char aChar = Serial.read();
        this->inData[index_serial_data] = aChar;
        this->index_serial_data++;
        if (aChar == '\n' || this->index_serial_data == N_SERIAL_DATA_STR - 1)
        {
          /**
             if previously there was an incomplete line
             ignore the line AND the next line (until the next \n)
          */
          uint8_t read_line = 1;
          if (this->incomplete_line) {
            this->incomplete_line = 0;
            read_line = 0;
          }
          if (aChar != '\n') {
            this->incomplete_line = 1;
            read_line = 0;
          }
          this->inData[this->index_serial_data] = '\0';

          if (read_line) {
            //            Serial.print("254, Read line: ");
            //            Serial.println(this->inData);
            int nparse = this->parseCSV(this->inData, this->dataArray, N_SERIAL_DATA_VAL);
            int cmd = this->dataArray[0];
            (*onparse)(cmd, this->dataArray);
          }
          else
          {
            //            Serial.print("254, Skip line: ");
            //            Serial.println(this->inData);
          }

          this->inData[index_serial_data] = '\0'; // Keep the string NULL terminated
          this->index_serial_data = 0;
          this->inData[0] = '\0';
        }
      }

    }
};
