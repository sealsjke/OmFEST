FROM golang:alpine AS builder

WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o /app/longlisten .

FROM alpine:3.20

RUN apk --no-cache add ca-certificates tzdata

WORKDIR /app
COPY --from=builder /app/longlisten .

ENV FLAG="OmFEST{qu4ck_m3tr0p0l1s_l1ghts_1gn1t3d_by_y3ll0w_duck}" \
    CALLING_MESSAGE="Quack. Chief Architect to lights. The yellow one knows." \
    USER_NAME="yellow_duck" \
    USER_PASSWORD="michael" \
    FLAG_TOPIC="digital_omsk/lights" \
    BROADCAST_INTERVAL="1m"

EXPOSE 1883

CMD ["./longlisten"]
