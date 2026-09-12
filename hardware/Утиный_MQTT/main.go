package main

import (
	"bytes"
	"context"
	"fmt"
	"log"
	"os"
	"os/signal"
	"sort"
	"strings"
	"sync"
	"syscall"
	"time"

	mqtt "github.com/mochi-mqtt/server/v2"
	"github.com/mochi-mqtt/server/v2/listeners"
	"github.com/mochi-mqtt/server/v2/packets"
)

// Config stores application configuration parsed from environment variables.
type Config struct {
	Flag              string
	CallingMessage    string
	UserName          string
	UserPassword      string
	FlagTopic         string
	BroadcastInterval time.Duration
	ListenAddr        string
}

func loadConfig() Config {
	flag := getEnv("FLAG", "OmFEST{qu4ck_m3tr0p0l1s_l1ghts_1gn1t3d_by_y3ll0w_duck}")
	userName := getEnv("USER_NAME", "yellow_duck")
	userPassword := getEnv("USER_PASSWORD", "1234567")
	flagTopic := getEnv("FLAG_TOPIC", "duckpolis/lights")
	listenAddr := getEnv("LISTEN_ADDR", ":1883")

	callingMsgRaw := os.Getenv("CALLING_MESSAGE")
	var callingMessage string
	if callingMsgRaw != "" {
		callingMessage = callingMsgRaw
	} else {
		callingMessage = fmt.Sprintf("Quack! Automated dispatch: Energy grid is waiting for the Chief Architect of digital Omsk to report to topic %s! Who designed our metropolis? The yellow duck!", flagTopic)
	}

	interval := 1 * time.Minute
	if intervalStr := os.Getenv("BROADCAST_INTERVAL"); intervalStr != "" {
		if parsed, err := time.ParseDuration(intervalStr); err == nil && parsed > 0 {
			interval = parsed
		} else {
			log.Printf("Warning: invalid BROADCAST_INTERVAL %q, defaulting to 1m", intervalStr)
		}
	}

	return Config{
		Flag:              flag,
		CallingMessage:    callingMessage,
		UserName:          userName,
		UserPassword:      userPassword,
		FlagTopic:         flagTopic,
		BroadcastInterval: interval,
		ListenAddr:        listenAddr,
	}
}

func getEnv(key, defaultVal string) string {
	if val := os.Getenv(key); val != "" {
		return val
	}
	return defaultVal
}

// TopicTracker maintains a thread-safe registry of active topics in the broker.
type TopicTracker struct {
	mu     sync.RWMutex
	topics map[string]struct{}
}

func NewTopicTracker() *TopicTracker {
	tracker := &TopicTracker{
		topics: make(map[string]struct{}),
	}
	// Initial default public topics so wildcard subscribers always receive messages
	defaultTopics := []string{
		"general",
		"broadcast",
		"announcements",
		"alerts",
		"chat",
		"system/status",
	}
	for _, t := range defaultTopics {
		tracker.topics[t] = struct{}{}
	}
	return tracker
}

func (t *TopicTracker) Add(topic string) {
	if topic == "" {
		return
	}
	t.mu.Lock()
	defer t.mu.Unlock()
	t.topics[topic] = struct{}{}
}

func (t *TopicTracker) GetAll(server *mqtt.Server, flagTopic string) []string {
	t.mu.Lock()
	defer t.mu.Unlock()

	// Discover any active client subscription filters
	if server != nil && server.Clients != nil {
		for _, cl := range server.Clients.GetAll() {
			if cl.State.Subscriptions != nil {
				for filter := range cl.State.Subscriptions.GetAll() {
					if !strings.Contains(filter, "#") && !strings.Contains(filter, "+") && filter != flagTopic && !strings.HasPrefix(filter, "$") {
						t.topics[filter] = struct{}{}
					}
				}
			}
		}
	}

	result := make([]string, 0, len(t.topics))
	for k := range t.topics {
		if k != flagTopic && !strings.Contains(k, "#") && !strings.Contains(k, "+") && !strings.HasPrefix(k, "$") {
			result = append(result, k)
		}
	}
	sort.Strings(result)
	return result
}

// AuthHook implements authentication and ACL checks for MQTT clients.
type AuthHook struct {
	mqtt.HookBase
	userName     string
	userPassword string
	flagTopic    string
	topics       *TopicTracker
}

func (h *AuthHook) ID() string {
	return "longlisten-auth"
}

func (h *AuthHook) Provides(b byte) bool {
	return bytes.Contains([]byte{
		mqtt.OnConnectAuthenticate,
		mqtt.OnACLCheck,
		mqtt.OnSubscribe,
		mqtt.OnPublish,
	}, []byte{b})
}

// OnConnectAuthenticate verifies credentials when USER_NAME connects.
// Non-target users and anonymous connections are permitted so players can explore.
func (h *AuthHook) isTargetUser(username string) bool {
	return username == h.userName || username == "yellowduck" || username == "duck"
}

// OnConnectAuthenticate verifies credentials when target user connects.
// Non-target users and anonymous connections are permitted so players can explore.
func (h *AuthHook) OnConnectAuthenticate(cl *mqtt.Client, pk packets.Packet) bool {
	username := string(pk.Connect.Username)
	if h.isTargetUser(username) {
		if string(pk.Connect.Password) != h.userPassword {
			log.Printf("Authentication failed for user %q from %s", username, cl.Net.Remote)
			return false
		}
		log.Printf("Authentication successful for user %q from %s", username, cl.Net.Remote)
		return true
	}

	// Anonymous or other usernames allowed to connect
	return true
}

// OnACLCheck enforces access control:
// - Server inline client is always allowed.
// - Target user is allowed full access to flagTopic and all topics.
// - Other users are allowed access to public topics, but denied access to flagTopic.
func (h *AuthHook) OnACLCheck(cl *mqtt.Client, topic string, write bool) bool {
	if cl.Net.Inline {
		return true
	}

	isUser := h.isTargetUser(string(cl.Properties.Username))
	if isUser {
		return true
	}

	// For non-authorized users, check if topic is or targets the secret flag topic
	if h.isFlagTopicOrSub(topic) {
		return false
	}

	return true
}

func (h *AuthHook) isFlagTopicOrSub(topic string) bool {
	if topic == h.flagTopic {
		return true
	}
	// Check wildcard targets specifically scoping the flagTopic (e.g. "secret/#" or "secret/+")
	if strings.HasSuffix(topic, "/#") || strings.HasSuffix(topic, "/+") {
		prefix := topic[:len(topic)-2]
		if strings.HasPrefix(h.flagTopic, prefix+"/") || h.flagTopic == prefix {
			return true
		}
	}
	return false
}

// OnSubscribe records any newly subscribed specific topics to our registry.
func (h *AuthHook) OnSubscribe(cl *mqtt.Client, pk packets.Packet) packets.Packet {
	for _, sub := range pk.Filters {
		if !strings.Contains(sub.Filter, "#") && !strings.Contains(sub.Filter, "+") && sub.Filter != h.flagTopic && !strings.HasPrefix(sub.Filter, "$") {
			h.topics.Add(sub.Filter)
		}
	}
	return pk
}

// OnPublish records any topics published to by clients.
func (h *AuthHook) OnPublish(cl *mqtt.Client, pk packets.Packet) (packets.Packet, error) {
	if !strings.HasPrefix(pk.TopicName, "$") && pk.TopicName != h.flagTopic {
		h.topics.Add(pk.TopicName)
	}
	return pk, nil
}

func main() {
	cfg := loadConfig()

	log.Printf("Starting LongListen MQTT Broker...")
	log.Printf("Configured USER_NAME: %s", cfg.UserName)
	log.Printf("Configured FLAG_TOPIC: %s", cfg.FlagTopic)
	log.Printf("Configured BROADCAST_INTERVAL: %s", cfg.BroadcastInterval)

	topicTracker := NewTopicTracker()

	server := mqtt.New(&mqtt.Options{
		InlineClient: true,
	})

	authHook := &AuthHook{
		userName:     cfg.UserName,
		userPassword: cfg.UserPassword,
		flagTopic:    cfg.FlagTopic,
		topics:       topicTracker,
	}

	if err := server.AddHook(authHook, nil); err != nil {
		log.Fatalf("Failed to add auth hook: %v", err)
	}

	tcp := listeners.NewTCP(listeners.Config{
		ID:      "t1",
		Address: cfg.ListenAddr,
	})
	if err := server.AddListener(tcp); err != nil {
		log.Fatalf("Failed to add listener: %v", err)
	}

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// Periodic broadcaster: sends calling message on all topics and flag on flagTopic every BroadcastInterval
	go func() {
		ticker := time.NewTicker(cfg.BroadcastInterval)
		defer ticker.Stop()

		for {
			select {
			case <-ticker.C:
				topics := topicTracker.GetAll(server, cfg.FlagTopic)
				for _, topic := range topics {
					if err := server.Publish(topic, []byte(cfg.CallingMessage), false, 0); err != nil {
						log.Printf("Error broadcasting calling message to topic %q: %v", topic, err)
					}
				}

				// Publish flag strictly to the secret topic
				if err := server.Publish(cfg.FlagTopic, []byte(cfg.Flag), false, 0); err != nil {
					log.Printf("Error broadcasting flag to topic %q: %v", cfg.FlagTopic, err)
				}

				log.Printf("Broadcast cycle complete: sent calling message to %d topics and flag to %s", len(topics), cfg.FlagTopic)
			case <-ctx.Done():
				return
			}
		}
	}()

	go func() {
		log.Printf("MQTT broker listening on %s", cfg.ListenAddr)
		if err := server.Serve(); err != nil {
			log.Fatalf("Server error: %v", err)
		}
	}()

	stop := make(chan os.Signal, 1)
	signal.Notify(stop, os.Interrupt, syscall.SIGTERM)
	<-stop

	log.Println("Shutting down broker...")
	cancel()
	_ = server.Close()
	log.Println("Broker stopped")
}
