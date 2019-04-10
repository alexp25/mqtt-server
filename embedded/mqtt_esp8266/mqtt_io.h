
void formatOutput(int* array_data, int len, char* buf) {
  char buf1[10];
  for (int i = 0; i < len; i++) {
    sprintf(buf1, "%d", array_data[i]);
    if (i == 0) {
      strcpy(buf, buf1);
    } else {
      strcat(buf, buf1);
    }
    if (i < len - 1) {
      strcat(buf, ",");
    }
  }
}

