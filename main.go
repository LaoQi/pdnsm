package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"

	"github.com/akamensky/argparse"
)

// Config config
type Config struct {
	Port  *int
	Hosts *string
}

// HostsItem hostsitem
type HostsItem struct {
	IP     string `json:"ip"`
	Domain string `json:"domain"`
}

// Hosts hosts
type Hosts struct {
	Body []HostsItem
	Path string
}

func (h *Hosts) load() {
	f, err := os.Open(h.Path)
	if err != nil {
		log.Printf("Warning: cannot read hosts file at %s, %s", h.Path, err.Error())
	}
}

var hosts *Hosts

func apiHosts(w http.ResponseWriter, req *http.Request) {
	out, err := json.Marshal(hosts.Body)
	if err != nil {
		log.Printf("Warning: %s", err.Error())
	}
	w.Write(out)
}

func main() {

	parser := argparse.NewParser("pdnsm", "DNS WebUI service")

	config := Config{}
	config.Port = parser.Int("p", "port", &argparse.Options{Default: 8000, Help: "set port"})
	config.Hosts = parser.String("f", "hosts", &argparse.Options{Default: "/etc/hosts", Help: "Hosts file path"})
	err := parser.Parse(os.Args)
	if err != nil {
		fmt.Print(parser.Usage(err))
		os.Exit(2)
	}

	// initialization
	hosts = &Hosts{
		Body: make([]HostsItem, 0),
		Path: *config.Hosts,
	}
	hosts.load()

	// http.HandleFunc("/test", handle)
	http.HandleFunc("/api/hosts", apiHosts)
	http.Handle("/", http.FileServer(http.Dir("./public")))

	log.Fatal(http.ListenAndServe(fmt.Sprintf(":%d", *config.Port), nil))
	os.Exit(0)
}
