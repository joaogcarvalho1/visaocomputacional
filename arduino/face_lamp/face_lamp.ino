/* Arduino Uno: controle de módulo relé 5 V por USB serial (9600 baud).
 * ON\n -> ACK ON\n; OFF\n -> ACK OFF\n.
 * Sem comando válido por 3 segundos, desliga o relé.
 * Use módulo relé com driver; nunca conecte uma bobina diretamente ao pino.
 */
#include <string.h>

const byte RELAY_PIN = 8;
const bool RELAY_ACTIVE_LOW = true;  // Ajuste conforme o seu módulo.
const unsigned long WATCHDOG_MS = 3000;
char command[8];
byte commandLength = 0;
bool overflow = false;
bool lampOn = false;
unsigned long lastCommand = 0;

void setLamp(bool enabled) {
  lampOn = enabled;
  digitalWrite(RELAY_PIN, (enabled == RELAY_ACTIVE_LOW) ? LOW : HIGH);
  digitalWrite(LED_BUILTIN, enabled ? HIGH : LOW);
}

void setup() {
  // Prepara o nível de desligamento antes de habilitar a saída.
  digitalWrite(RELAY_PIN, RELAY_ACTIVE_LOW ? HIGH : LOW);
  pinMode(RELAY_PIN, OUTPUT);
  pinMode(LED_BUILTIN, OUTPUT);
  setLamp(false);
  Serial.begin(9600);
}

void loop() {
  while (Serial.available() > 0) {
    char value = Serial.read();
    if (value == '\r') continue;
    if (value == '\n') {
      command[commandLength] = '\0';
      if (!overflow && strcmp(command, "ON") == 0) {
        setLamp(true);
        lastCommand = millis();
        Serial.println("ACK ON");
      } else if (!overflow && strcmp(command, "OFF") == 0) {
        setLamp(false);
        lastCommand = millis();
        Serial.println("ACK OFF");
      } else {
        Serial.println("ERR");
      }
      commandLength = 0;
      overflow = false;
    } else if (!overflow && commandLength < sizeof(command) - 1) {
      command[commandLength++] = value;
    } else {
      overflow = true;
    }
  }
  if (lampOn && millis() - lastCommand >= WATCHDOG_MS) {
    setLamp(false);
  }
}
