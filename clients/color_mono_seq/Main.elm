module Main exposing (..)

import Html exposing (div, Html, text)
import Html.Attributes exposing (class)
import Html.Events exposing (onClick)
import WebSocket
import Json.Encode exposing (object, encode)
import Json.Decode exposing (int, field, list, Decoder, decodeString)
import Json.Decode.Pipeline exposing (decode, required, optional, hardcoded)


main =
    Html.programWithFlags
        { init = init
        , view = view
        , update = update
        , subscriptions = subscriptions
        }


type alias Flags =
    { websocketHost : String }


host =
    "127.0.0.1"


url =
    "ws://" ++ host ++ ":7700/colormonosequencer"



-- MODEL


type alias Model =
    { notes : List Note
    }


init : Flags -> ( Model, Cmd Msg )
init fs =
    ( Model [ Note Do, Note Re, Note Mi, Note Fa ], WebSocket.send url <| encode 0 getState )


baseDo : Int
baseDo =
    60


re =
    baseDo + 2


mi =
    baseDo + 4


fa =
    baseDo + 5


intToPitch : Int -> Pitch
intToPitch x =
    if x == baseDo then
        Do
    else if x == re then
        Re
    else if x == mi then
        Mi
    else
        Fa


pitchToInt : Pitch -> Int
pitchToInt pitch =
    case pitch of
        Do ->
            baseDo

        Re ->
            baseDo + 2

        Mi ->
            baseDo + 4

        Fa ->
            baseDo + 5


type Pitch
    = Do
    | Re
    | Mi
    | Fa


type alias Note =
    { pitch : Pitch
    }



-- UPDATE


type Msg
    = ChangeNote Int Pitch
    | RcvState String


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        ChangeNote i pitch ->
            ( updateNotes i pitch model, WebSocket.send url <| encode 0 <| changePitchWSMsg i (pitchToInt pitch) )

        RcvState str ->
            ( decodeWSMsg str model, Cmd.none )


cyclePitch : Pitch -> Pitch
cyclePitch pitch =
    if pitch == Do then
        Re
    else if pitch == Re then
        Mi
    else if pitch == Mi then
        Fa
    else if pitch == Fa then
        Do
    else
        Do


updateNotes : Int -> Pitch -> Model -> Model
updateNotes index newPitch model =
    let
        newNote i note =
            if i == index then
                { note | pitch = newPitch }
            else
                note
    in
        { model | notes = List.indexedMap newNote model.notes }



-- SUBSCRIPTIONS


subscriptions : Model -> Sub Msg
subscriptions model =
    WebSocket.listen url RcvState



-- VIEW


view : Model -> Html Msg
view model =
    div [ class "container" ] [ viewNotes model.notes ]


viewNotes : List Note -> Html Msg
viewNotes notes =
    div [ class "notes" ] (List.indexedMap viewNote notes)


viewNote : Int -> Note -> Html Msg
viewNote i note =
    let
        newPitch =
            cyclePitch note.pitch
    in
        div [ class "note", onClick <| ChangeNote i newPitch ] [ text <| toString <| pitchToInt note.pitch ]



-- COMMANDS


changePitchWSMsg index value =
    object
        [ ( "kind", Json.Encode.string "pitch" )
        , ( "payload"
          , object
                [ ( "index", Json.Encode.int index )
                , ( "value", Json.Encode.int value )
                ]
          )
        ]


type alias BeatMsg =
    { payload : BeatMsgPayload
    }


type alias BeatMsgPayload =
    { rthythmIndex : Int
    , noteIndex : Int
    }


type alias StateMsgPayload =
    { pitches : List Int
    , rhythm : List Int
    }


type alias StateMsg =
    { payload : StateMsgPayload
    }


type WSMsg
    = Beat
    | State


getState : Json.Encode.Value
getState =
    object [ ( "kind", Json.Encode.string "state" ) ]


determineTypeOfWSMsg : String -> WSMsg
determineTypeOfWSMsg msg =
    case decodeString (field "action" Json.Decode.string) msg of
        Ok "state" ->
            State

        Ok "beat" ->
            Beat

        _ ->
            Debug.crash "Unexpected msg kind!"


decodeBeatMsg : Decoder BeatMsg
decodeBeatMsg =
    let
        payloadDecoder =
            decode BeatMsgPayload
                |> required "rhythm_index" int
                |> required "note_index" int
    in
        decode BeatMsg
            |> required "payload" payloadDecoder


decodeStateMsg : Decoder StateMsg
decodeStateMsg =
    let
        payloadDecoder =
            decode StateMsgPayload
                |> required "pitches" (list int)
                |> required "rhythm" (list int)
    in
        decode StateMsg
            |> required "payload" payloadDecoder


decodeWSMsg : String -> Model -> Model
decodeWSMsg msg =
    let
        kind =
            determineTypeOfWSMsg msg

        updateBeat beat model =
            model

        updateState newState model =
            { model | notes = newState.payload.pitches |> List.map (intToPitch >> Note) }

        payloadDecoder =
            case kind of
                State ->
                    case decodeString decodeStateMsg msg of
                        Ok msg ->
                            updateState msg

                        _ ->
                            Debug.crash ""

                Beat ->
                    case decodeString decodeBeatMsg msg of
                        Ok msg ->
                            updateBeat msg

                        _ ->
                            Debug.crash ""
    in
        payloadDecoder
