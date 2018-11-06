package main

import (
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

func handle(w http.ResponseWriter, req *http.Request) {
}

func main() {

	parser := argparse.NewParser("DNSWUI", "DNS WebUI service")

	config := Config{}
	config.Port = parser.Int("p", "port", &argparse.Options{Default: 8000, Help: "set port"})
	config.Hosts = parser.String("h", "hosts", &argparse.Options{Default: "/etc/hosts", Help: "Hosts file path"})
	err := parser.Parse(os.Args)
	if err != nil {
		fmt.Print(parser.Usage(err))
		os.Exit(2)
	}

	http.HandleFunc("/test", handle)
	http.Handle("/", http.FileServer(http.Dir("./public")))

	log.Fatal(http.ListenAndServe(fmt.Sprintf(":%d", *config.Port), nil))
	os.Exit(0)
}
