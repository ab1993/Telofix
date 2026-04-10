package org.agilonhealth.agenticbugresolvertool.controller;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.io.BufferedReader;
import java.io.File;
import java.io.InputStreamReader;
import java.util.concurrent.ConcurrentHashMap;

@RestController
@RequestMapping("/webhook")
public class JiraWebhookController {

    // Tracks active tickets to prevent duplicate runs
    private static final ConcurrentHashMap<String, Boolean> activeTickets = new ConcurrentHashMap<>();

    @PostMapping("/jira-trigger")
    public ResponseEntity<String> handleJiraEvent(@RequestBody String jiraPayload) {
        try {
            ObjectMapper mapper = new ObjectMapper();
            JsonNode payload = mapper.readTree(jiraPayload);

            String issueKey = "UNKNOWN";
            String issueId = "Default";
            String summary = "No summary";
            String description = "No description";
            String ticketLink = "N/A";

            // 1. Extract Data (Handling both Custom and Default Jira formats)
            if (payload.has("issueKey")) {
                issueKey = payload.get("issueKey").asText();
                summary = payload.has("summary") ? payload.get("summary").asText() : "No summary";
                description = payload.has("description") ? payload.get("description").asText() : "No description";
            } else if (payload.has("issue") && payload.get("issue").has("key")) {
                issueKey = payload.get("issue").get("key").asText();
                issueId = payload.get("issue").get("id").asText();
                ticketLink = payload.get("issue").get("self").asText();
                JsonNode fields = payload.get("issue").get("fields");
                if (fields != null) {
                    summary = fields.has("summary") ? fields.get("summary").asText() : "No summary";
                    JsonNode descNode = fields.get("description");
                    if (descNode != null && !descNode.isNull()) {
                        description = descNode.toString();
                    }
                }
            }

            // 2. The Gatekeeper: Ignore pings and non-ticket events completely invisibly
            if (issueKey.equals("UNKNOWN") || issueKey.isEmpty()) {
                return ResponseEntity.ok("Ignored non-ticket request.");
            }

            // 3. Deduplication Check (Ignore duplicate webhooks from Jira)
            if (activeTickets.containsKey(issueKey)) {
                System.out.println("⚠️ Already processing " + issueKey + ". Ignoring duplicate webhook.");
                return ResponseEntity.ok("Duplicate request ignored.");
            }
            activeTickets.put(issueKey, true);

            // 4. DEMO LOGGING (Beautiful and clear for leadership)
            System.out.println("\n=================================================");
            System.out.println("🔔 WEBHOOK RECEIVED FROM JIRA");
            System.out.println("=================================================");
            System.out.println("🎫 SCRUM OR SPRINT: " + issueKey);
            System.out.println("🎫 TICKET ID MINT-" + issueId);
            System.out.println("🎫 JIRA LINK: " + ticketLink);
            System.out.println("📝 SUMMARY: " + summary);

            System.out.println("-------------------------------------------------");

            // Prepare the payload for Python
            String aiTask = "Ticket Summary: " + summary + "\nTicket Description: " + description;
            final String finalIssueKey = issueKey;

            // 5. Start Agent in Background Thread
            new Thread(() -> {
                try {
                    System.out.println("🚀 Waking up AI Agent process in background...");
                    ProcessBuilder pb = new ProcessBuilder("venv/bin/python", "-u", "agent.py", finalIssueKey, aiTask);
                    pb.directory(new File(System.getProperty("user.dir")));
                    pb.redirectErrorStream(true);

                    Process process = pb.start();

                    BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));
                    String line;
                    while ((line = reader.readLine()) != null) {
                        System.out.println("[AGENT]: " + line);
                    }
                    process.waitFor();
                } catch (Exception e) {
                    System.err.println("❌ Background process failed:");
                    e.printStackTrace();
                } finally {
                    // Clean up when done so we can test the same ticket again later if needed
                    activeTickets.remove(finalIssueKey);
                    System.out.println("✅ Task completed. Cleaned up " + finalIssueKey);
                }
            }).start();

            // 6. Return 200 OK instantly to Jira so it doesn't loop
            return ResponseEntity.ok("Agent triggered successfully for " + issueKey);

        } catch (Exception e) {
            e.printStackTrace();
            return ResponseEntity.internalServerError().body("Failed to process webhook");
        }
    }
}